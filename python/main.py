import asyncio
import statistics
import time

from lib import python_asyncio
from py03_benchmark.py03_benchmark import (
    rust_tokio_with_async_runtimes,
    rust_tokio_with_pyo3,
)


async def call_rust_tokio_with_pyo3(calls: int, l: list[tuple[int, int]]):
    tasks = [asyncio.create_task(rust_tokio_with_pyo3(l)) for c in range(calls)]
    _ = await asyncio.gather(*tasks)
    return


async def call_python_asyncio(calls: int, l: list[tuple[int, int]]):
    tasks = [asyncio.create_task(python_asyncio(l)) for c in range(calls)]
    _ = await asyncio.gather(*tasks)
    return


async def call_rust_tokio_with_async_runtimes(calls: int, l: list[tuple[int, int]]):
    tasks = [rust_tokio_with_async_runtimes(l) for c in range(calls)]
    _ = await asyncio.gather(*tasks)
    return


async def measure(calls: int, size: int, function, type: str, lang: str):
    times = []

    l = [(i, i + 1) for i in range(size)]
    for _ in range(10):
        start = time.perf_counter()
        _ = await function(calls, l)
        times.append(time.perf_counter() - start)

    mean_t = statistics.mean(times)
    std_t = statistics.stdev(times)

    print(
        f"{type} {lang} with {calls} calls and list size {size}: "
        f"mean={mean_t:.6f}s, std={std_t:.6f}s"
    )


async def main():
    print("py03-benchmark")

    call_size_list = [
        (150000, 8),
        (2500, 1000),
        (5, 200000),
    ]

    print("Benchmark\n")

    for calls, size in call_size_list:
        await measure(
            calls,
            size,
            call_rust_tokio_with_async_runtimes,
            "Tokio with Async Runtimes",
            "Rust",
        )
        await measure(calls, size, call_rust_tokio_with_pyo3, "Tokio with PyO3", "Rust")
        await measure(calls, size, call_python_asyncio, "Asyncio", "Python")


if __name__ == "__main__":
    asyncio.run(main())
