import time
import asyncio
from typing import Any

from scylla_python_serialization._rust.session_builder import (
    SessionBuilder as PySessionBuilder,
)
from scylla_python_serialization._rust.session import (
    PyPreparedStatement,
    PyRowSerializationContext,
    Session as PySession,
)

from scylla_python_serialization.serialize.serialize import (
    BigInt,
    Boolean,
    Double,
    Int,
    List,
    Text,
    UserDefinedType,
    ValueList,
)

from scylla_rust_python_serialization.serializer import SerializedValues
from scylla_rust_python_serialization._rust.session_builder import (
    SessionBuilder as RustPySessionBuilder,
)
from scylla_rust_python_serialization._rust.session import Session as RustPySession
from scylla_rust_python_serialization._rust.statements import (
    PyPreparedStatement as RustPyPreparedStatement,
)

from scylla_rust_serialization._rust.session import Session as RustSession
from scylla_rust_serialization._rust.session_builder import (
    SessionBuilder as RustSessionBuilder,
)
from scylla_rust_serialization._rust.session import (
    serialize_rust,
    serialize_rust_and_return,
    PyPreparedStatement as RustPreparedStatement,
)

PreparedStatements = tuple[
    PyPreparedStatement, RustPyPreparedStatement, RustPreparedStatement
]
Sessions = tuple[PySession, RustPySession, RustSession]


async def setup_session() -> Sessions:
    session_py = await PySessionBuilder(["127.0.0.2"], 9042).connect()

    session_rust_py = await RustPySessionBuilder(["127.0.0.2"], 9042).connect()

    session_rust = await RustSessionBuilder(["127.0.0.2"], 9042).connect()

    await session_py.execute("""
        CREATE KEYSPACE IF NOT EXISTS test_ks 
        WITH REPLICATION = {'class':'SimpleStrategy','replication_factor':1}
    """)

    await session_py.execute("USE test_ks")

    await session_rust_py.execute("USE test_ks")

    await session_rust.execute("USE test_ks")

    return session_py, session_rust_py, session_rust


async def create_table(
    sessions: Sessions,
    create_table_query: str,
    prepare_statement_query: str,
) -> PreparedStatements:
    await sessions[0].execute(create_table_query)

    prepared_py = await sessions[0].prepare(prepare_statement_query)
    prepared_rust_py = await sessions[1].prepare(prepare_statement_query)
    prepared_rust = await sessions[2].prepare(prepare_statement_query)

    return prepared_py, prepared_rust_py, prepared_rust


async def create_list_table(
    sessions: Sessions,
) -> PreparedStatements:
    create_list_query = """
                        CREATE TABLE IF NOT EXISTS table_with_list (
                                                                       id int PRIMARY KEY,
                                                                       scores list<int>
                        ) \
                        """

    prepared_statement_query = (
        "INSERT INTO test_ks.table_with_list (id, scores) VALUES (?, ?)"
    )

    return await create_table(sessions, create_list_query, prepared_statement_query)


async def create_string_table(
    sessions: Sessions,
) -> PreparedStatements:
    create_table_query = """
                         CREATE TABLE IF NOT EXISTS table_with_string (
                                                                          id int PRIMARY KEY,
                                                                          scores text
                         ) \
                         """

    prepared_statement_query = (
        "INSERT INTO test_ks.table_with_string (id, scores) VALUES (?, ?)"
    )

    return await create_table(sessions, create_table_query, prepared_statement_query)


async def create_many_ints_table(
    sessions: Sessions, num_cols: int = 50
) -> PreparedStatements:
    cols = ",\n".join([f"c{i} int" for i in range(num_cols)])
    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS table_with_{num_cols}_ints (
            id int PRIMARY KEY,
            {cols}
        )
    """

    placeholders = ", ".join(["?"] * (num_cols + 1))  # id + 50 ints
    col_names = ", ".join(["id"] + [f"c{i}" for i in range(num_cols)])

    prepared_statement_query = f"INSERT INTO test_ks.table_with_{num_cols}_ints ({col_names}) VALUES ({placeholders})"

    return await create_table(sessions, create_table_query, prepared_statement_query)


async def create_nested_list_table(
    sessions: Sessions, depth: int
) -> PreparedStatements:
    col_type = "int"
    for _ in range(depth):
        col_type = f"frozen<list<{col_type}>>"

    col_type = f"list<{col_type}>"

    table_name = f"table_with_nested_depth_{depth}"

    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id int PRIMARY KEY,
            scores {col_type}
        )
    """

    prepared_statement_query = (
        f"INSERT INTO test_ks.{table_name} (id, scores) VALUES (?, ?)"
    )

    return await create_table(sessions, create_table_query, prepared_statement_query)


async def create_wide_mixed_table(sessions: Sessions, width: int) -> PreparedStatements:
    table_name = f"table_wide_{width}_mixed"

    cols = []
    for i in range(width):
        cols.append(f"a{i} int")
        cols.append(f"b{i} text")
        cols.append(f"c{i} double")
        cols.append(f"d{i} boolean")
        cols.append(f"e{i} list<int>")

    col_def = ",\n".join(cols)

    create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id int PRIMARY KEY,
                {col_def}
            )
        """

    col_names = ["id"] + [c.split()[0] for c in cols]
    placeholders = ", ".join(["?"] * len(col_names))
    col_names_str = ", ".join(col_names)

    prepared_statement_query = (
        f"INSERT INTO test_ks.{table_name} ({col_names_str}) VALUES ({placeholders})"
    )

    return await create_table(sessions, create_table_query, prepared_statement_query)


async def create_udt_table(
    sessions: Sessions,
) -> PreparedStatements:
    # Basic UDT
    await sessions[0].execute("""
        CREATE TYPE IF NOT EXISTS address (
            street text,
            zip int,
            coords list<double>
        )
    """)

    # Nested UDT
    await sessions[0].execute("""
        CREATE TYPE IF NOT EXISTS profile (
            name text,
            age int,
            addr frozen<address>
        )
    """)

    create_table_query = """
                         CREATE TABLE IF NOT EXISTS udt_table (
                                                                  id int PRIMARY KEY,
                                                                  data frozen<profile>
                         ) \
                         """

    prepared_statement_query = "INSERT INTO test_ks.udt_table (id, data) VALUES (?, ?)"

    return await create_table(sessions, create_table_query, prepared_statement_query)


def wrap(value: Any):
    """Convert a raw Python value into the correct SerializeValue wrapper."""

    if isinstance(value, bool):
        return Boolean(value)

    if isinstance(value, int):
        if -2147483648 <= value <= 2147483647:
            return Int(value)
        return BigInt(value)

    if isinstance(value, float):
        return Double(value)

    if isinstance(value, str):
        return Text(value)

    if isinstance(value, list):
        return List([wrap(v) for v in value])

    raise TypeError(f"Cannot wrap value {value!r} into a SerializeValue")


def wrap_udt(py_dict: dict):
    """Convert a Python dict into a UserDefinedType with wrapped fields."""

    wrapped_fields = {}

    for key, value in py_dict.items():
        if isinstance(value, dict):
            wrapped_fields[key] = wrap_udt(value)
        elif isinstance(value, list):
            wrapped_fields[key] = List([wrap(v) for v in value])
        else:
            wrapped_fields[key] = wrap(value)

    return UserDefinedType(wrapped_fields)


def make_pair(*raw_values: Any):
    """Return (normal_tuple, ValueList_with_wrapped_values)."""
    normal = tuple(raw_values)
    wrapped = [wrap(v) for v in raw_values]
    return normal, ValueList(wrapped)


def build_long_string_row(i: int, n: int):
    raw = i, "x" * n
    return make_pair(*raw)


def build_list_row(i: int, n: int):
    raw = i, [j for j in range(n)]
    return make_pair(*raw)


def build_many_ints_row(i: int, n: int = 50):
    raw = i, *range(n)
    return make_pair(*raw)


def make_nested(depth: int):
    lst = [1]

    for _ in range(depth):
        lst = [lst for _ in range(2)]

    return lst


def build_nested_list_row(i: int, depth: int = 3):
    raw = i, make_nested(depth)
    return make_pair(*raw)


def build_wide_mixed_row(i: int, width: int):
    values = [i]

    for g in range(width):
        values.append(g)
        values.append(f"text_{g}")
        values.append(float(g) + 0.123)
        values.append(g % 2 == 0)
        values.append([0, 1, 2])

    raw = tuple(values)
    return make_pair(*raw)


def build_udt_row(i: int, size: int):
    value = {
        "name": f"user_{i}",
        "age": 20 + (i % 10),
        "addr": {"street": f"Street {i}", "zip": 10000 + i, "coords": [52.234, 21.001]},
    }
    raw = i, value
    wrapped_udt = wrap_udt(value)

    return raw, ValueList([wrap(i), wrapped_udt])


def compare_serializations(
    values: Any,
    values_vl: ValueList,
    prepared: PreparedStatements,
) -> None:
    rust_py_ser = SerializedValues(prepared[1])
    rust_py_ser.add_row(values)
    rust_py_bytes, rust_py_count = rust_py_ser.get_content().get_elements()

    ctx = PyRowSerializationContext.from_prepared(prepared[0])
    row_ctx = ctx.get_context()
    py_bytes, py_count = values_vl.serialize(row_ctx)

    rust_count, rust_bytes = serialize_rust_and_return(values, prepared[2])

    print("\n=== Serialization Comparison ===")
    print(
        f"[Python]---[Rust-Python] | Content equal : {rust_py_bytes == py_bytes} | Element count equal: {rust_py_count == py_count}"
    )
    print(
        f"[Python]---[Rust]        | Content equal : {rust_bytes == py_bytes}   | Element count equal: {rust_count == py_count}"
    )
    print(
        f"[Rust]---[Rust-Python]   | Content equal : {rust_py_bytes == rust_bytes} | Element count equal: {rust_py_count == rust_count}"
    )
    print("--------------------------------")


def benchmark(
    calls: int,
    values: Any,
    values_vl: ValueList,
    size: int,
    prepared: PreparedStatements,
    test_type: str,
):
    print(f"Starting (size={size}) and calls={calls}")

    start = time.perf_counter()
    for i in range(calls):
        rust_py_ser = SerializedValues(prepared[1])
        rust_py_ser.add_row(values)
        _ = rust_py_ser.get_content()

    time_rust_py = time.perf_counter() - start

    print(
        f"[Rust-Python] Single serialization of type={test_type} (size={size}) took {time_rust_py:.6f}s"
    )

    start = time.perf_counter()
    for i in range(calls):
        ctx = PyRowSerializationContext.from_prepared(prepared[0])
        row_ctx = ctx.get_context()
        values_vl.serialize(row_ctx)
    time_py = time.perf_counter() - start

    print(
        f"[Python] Single serialization of type={test_type} (size={size}) took {time_py:.6f}s"
    )

    start = time.perf_counter()
    for i in range(calls):
        serialize_rust(values, prepared[2])
    time_rust = time.perf_counter() - start

    print(
        f"[Rust] Single serialization of type={test_type} (size={size}) took {time_rust:.6f}s"
    )

    return time_py


async def run_benchmark_case(
    create_values,
    prepared: PreparedStatements,
    typ: str,
    scenarios,
):
    results = []

    print("\n--------------" + typ + "---------------")
    for i, (calls, size) in enumerate(scenarios):
        values, values_vl = create_values(i, size)
        print(f"\n--- Benchmark: calls={calls}, size={size} ---")
        res = benchmark(calls, values, values_vl, size, prepared, typ)
        results.append(res)
        compare_serializations(values, values_vl, prepared)


async def run_benchmarks_single_schema(
    create_values, create_scheme, typ, scenarios, sessions
):
    prepared = await create_scheme(sessions)
    await run_benchmark_case(create_values, prepared, typ, scenarios)


async def run_benchmarks_multi_schema(
    create_values, create_scheme, typ, scenarios, session
):
    for calls, col_num in scenarios:
        prepared = await create_scheme(session, col_num)
        await run_benchmark_case(
            create_values,
            prepared,
            typ + f"size: {col_num}",
            [(calls, col_num)],
        )


async def main():
    sessions = await setup_session()

    scenarios = [
        (1, 20000000),
        (4000000, 1),
        (25000, 10000),
    ]

    await run_benchmarks_single_schema(
        build_list_row, create_list_table, "List ", scenarios, sessions
    )

    scenarios = [
        (1, 2000000000),
        (4000000, 2),
        (25000, 1000000),
    ]

    await run_benchmarks_single_schema(
        build_long_string_row, create_string_table, "String ", scenarios, sessions
    )

    scenarios = [
        (400000, 1),
    ]

    await run_benchmarks_single_schema(
        build_udt_row, create_udt_table, "UDT ", scenarios, sessions
    )

    scenarios = [
        (1, 500),
        (1, 1000),
        (1, 5000),
    ]

    await run_benchmarks_multi_schema(
        build_many_ints_row,
        create_many_ints_table,
        "Many ints table  ",
        scenarios,
        sessions,
    )

    scenarios = [
        (1, 18),
        (1, 20),
        (1, 23),
    ]

    await run_benchmarks_multi_schema(
        build_nested_list_row,
        create_nested_list_table,
        "Nested list ",
        scenarios,
        sessions,
    )

    scenarios = [
        (100, 500),
        (100, 2000),
        (100, 5000),
    ]

    await run_benchmarks_multi_schema(
        build_wide_mixed_row,
        create_wide_mixed_table,
        "Mixed table  ",
        scenarios,
        sessions,
    )


if __name__ == "__main__":
    asyncio.run(main())
