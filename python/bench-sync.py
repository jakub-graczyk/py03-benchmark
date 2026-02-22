import asyncio
import os
import threading
import time
import statistics
from typing import Any

from scylla_rs.session_builder import SessionBuilder as RsSessionBuilder
from scylla_rs.session import Session as RsSession

from cassandra.cluster import Cluster

SCYLLA_URI = os.getenv("SCYLLA_URI", "127.0.0.2:9042")


async def setup_session():
    host, port_s = SCYLLA_URI.split(":")
    port = int(port_s)

    rust_session = await RsSessionBuilder([host], port).connect()

    cluster = Cluster([host], port=port)
    cass_session = cluster.connect()

    await rust_session.execute("""
        CREATE KEYSPACE IF NOT EXISTS test_ks 
        WITH REPLICATION = {'class':'SimpleStrategy','replication_factor':1}
    """)

    await rust_session.execute("USE test_ks")
    cass_session.execute("USE test_ks")

    return rust_session, cass_session


async def create_table(
        sessions,
        create_table_query: str,
        insert_query: str,
        select_query: str,
):
    await sessions[0].execute(create_table_query)

    insert_rust = await sessions[0].prepare(insert_query)
    insert_cass = sessions[1].prepare(insert_query)

    select_rust = await sessions[0].prepare(select_query)
    select_cass = sessions[1].prepare(select_query)

    return insert_rust, insert_cass, select_rust, select_cass


async def create_list_table(sessions):
    table_name = "table_with_list"

    create_list_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id int PRIMARY KEY,
            scores list<int>
        )
    """

    insert_query = f"INSERT INTO test_ks.{table_name} (id, scores) VALUES (?, ?)"
    select_query = f"SELECT id, scores FROM test_ks.{table_name} WHERE id = ?"

    return await create_table(sessions, create_list_query, insert_query, select_query)


async def create_paging_int_table(sessions):
    table_name = "table_paging_int"

    create_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            pk int,
            ck int,
            v  int,
            PRIMARY KEY (pk, ck)
        ) WITH CLUSTERING ORDER BY (ck ASC)
    """

    insert_query = f"INSERT INTO test_ks.{table_name} (pk, ck, v) VALUES (?, ?, ?)"
    select_query = f"SELECT ck, v FROM test_ks.{table_name} WHERE pk = ?"

    return await create_table(sessions, create_query, insert_query, select_query)


def build_list_row(i: int, n: int) -> tuple:
    return (i, list(range(n)))


async def seed_rows(
        sessions,
        insert_rust,
        insert_cass,
        make_values,
        count: int,
        size: int,
        truncate_table: str | None = None,
):
    await sessions[0].execute("USE test_ks")
    sessions[1].execute("USE test_ks")

    if truncate_table:
        await sessions[0].execute(f"TRUNCATE {truncate_table}")
        sessions[1].execute(f"TRUNCATE {truncate_table}")

    for i in range(count):
        values = make_values(i, size)
        await sessions[0].execute(insert_rust, values)
        sessions[1].execute(insert_cass, values)


def force_materialize_scores(row: Any) -> int:
    """Touch every element of the 'scores' list column to force full deserialization."""
    if isinstance(row, dict) or hasattr(row, "__getitem__"):
        try:
            scores = row["scores"]
            n = len(scores)
            assert isinstance(scores, list)
            if n:
                _ = scores[0]
                _ = scores[-1]
            return n
        except Exception:
            pass

    scores = getattr(row, "scores", None)

    if scores is not None:
        n = len(scores)
        assert isinstance(scores, list)
        if n:
            _ = scores[0]
            _ = scores[-1]
        return n

    return 0


async def benchmarks_serialization(
        calls: int,
        size: int,
        prepared,
        bench_type: str,
        sessions,
        make_values,
):
    values = make_values(0, size)
    print(f"Starting SERIALIZATION (size={size}) calls={calls}")
    start = time.perf_counter()

    for _ in range(calls):
        _ = await sessions[0].execute(prepared[0], values)

    time_rust = time.perf_counter() - start
    print(f"[Rust] Single serialization of type={bench_type} (size={size}) took {time_rust:.6f}s")

    start = time.perf_counter()
    for i in range(calls):
        _ = sessions[1].execute(prepared[1], values)

    time_cass = time.perf_counter() - start
    print(f"[Python] Single serialization of type={bench_type} (size={size}) took {time_cass:.6f}s")

    return [time_rust, time_cass]


async def benchmarks_deserialization(
        calls: int,
        size: int,
        prepared,
        bench_type: str,
        sessions,
        make_values,
):
    insert_rust, insert_cass, select_rust, select_cass = prepared

    print(f"Starting DESER (size={size}) calls={calls}")

    rows_to_seed = calls
    await seed_rows(sessions, insert_rust, insert_cass, make_values, rows_to_seed, size)

    start = time.perf_counter()

    rs_totals = 0
    for i in range(calls):
        res = await sessions[0].execute(select_rust, (i % rows_to_seed,))
        row = await res.first()
        rs_totals += force_materialize_scores(row)

    time_rust = time.perf_counter() - start
    print(f"[Rust] DESER type={bench_type} size={size} took {time_rust:.6f}s (touched={rs_totals})")

    start = time.perf_counter()
    cass_totals = 0
    for i in range(calls):
        res = sessions[1].execute(select_cass, (i % rows_to_seed,))
        row = res.one()
        cass_totals += force_materialize_scores(row)

    time_cass = time.perf_counter() - start
    print(f"[Python] DESER type={bench_type} size={size} took {time_cass:.6f}s (touched={cass_totals})")

    return [time_rust, time_cass]


async def run_benchmark_case(
        create_values,
        prepared,
        bench_type: str,
        scenarios,
        sessions,
        bench_fn,
        repeats: int = 5,
):
    results = []
    print("\n--------------" + bench_type + "---------------")

    for calls, size in scenarios:
        rust_times = []
        cass_times = []

        for r in range(repeats):
            print(f"\n--- Benchmark: calls={calls}, size={size}, repeat={r + 1}/{repeats} ---")
            res = await bench_fn(calls, size, prepared, bench_type, sessions, create_values)
            results.append(res)
            rust_times.append(res[0])
            cass_times.append(res[1])

        rust_mean = statistics.mean(rust_times)
        cass_mean = statistics.mean(cass_times)
        rust_stdev = statistics.stdev(rust_times) if repeats > 1 else 0.0
        cass_stdev = statistics.stdev(cass_times) if repeats > 1 else 0.0

        print(
            f"\n>>> Summary (calls={calls}, size={size}, repeats={repeats})\n"
            f"    [Rust]   mean={rust_mean:.6f}s  stdev={rust_stdev:.6f}s\n"
            f"    [Python] mean={cass_mean:.6f}s  stdev={cass_stdev:.6f}s"
        )

    return results


async def run_bench_ser_deser(create_values, create_scheme, bench_type, scenarios, sessions):
    prepared = await create_scheme(sessions)

    print("\n=== SERIALIZATION ===")
    await run_benchmark_case(create_values, prepared, bench_type, scenarios, sessions, benchmarks_serialization)

    print("\n=== DESERIALIZATION ===")
    await run_benchmark_case(create_values, prepared, bench_type, scenarios, sessions, benchmarks_deserialization)


def _set_page_size(stmt, page_size: int):
    if hasattr(stmt, "set_page_size"):
        stmt.set_page_size(page_size)
    elif hasattr(stmt, "set_fetch_size"):
        stmt.set_fetch_size(page_size)
    return stmt


async def benchmarks_paging(
        calls: int,
        size: int,
        prepared,
        bench_type: str,
        sessions,
        make_values,
        page_size: int = 500,
        pk: int = 0,
):
    insert_rust, insert_cass, select_rust, select_cass = prepared

    print(f"Starting PAGING (rows={size}) scans={calls} page_size={page_size}")

    await seed_rows(
        sessions, insert_rust, insert_cass, make_values,
        count=size, size=size, truncate_table="table_paging_int",
    )

    start = time.perf_counter()
    for _ in range(calls):
        stmt_rust = _set_page_size(select_rust, page_size)
        res = await sessions[0].execute(stmt_rust, (pk,))
        rows = await res.all()
        if rows:
            _ = rows[0]
            _ = rows[-1]

    time_rust = time.perf_counter() - start
    print(f"[Rust] PAGING rows={size} scans={calls} took {time_rust:.6f}s")

    start = time.perf_counter()
    for _ in range(calls):
        bound = select_cass.bind((pk,))
        bound.fetch_size = page_size
        rows = sessions[1].execute(bound).all()
        if rows:
            _ = rows[0]
            _ = rows[-1]

    time_cass = time.perf_counter() - start
    print(f"[Python] PAGING rows={size} scans={calls} took {time_cass:.6f}s")

    return [time_rust, time_cass]


async def main():
    sessions = await setup_session()

    pk = 0
    paging_prepared = await create_paging_int_table(sessions)
    paging_scenarios = [
        (5, 10_000),
        (3, 100_000),
    ]

    await run_benchmark_case(
        create_values=lambda ck, _: (pk, ck, ck),
        prepared=paging_prepared,
        bench_type="Paging",
        scenarios=paging_scenarios,
        sessions=sessions,
        bench_fn=benchmarks_paging,
    )

    list_scenarios = [
        (10, 20000),
        (40000, 1),
        (2500, 100),
    ]

    await run_bench_ser_deser(
        build_list_row, create_list_table, "List", list_scenarios, sessions
    )


if __name__ == "__main__":
    asyncio.run(main())
