import asyncio
import os
import time
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
from lib import (
    async_collection_add_python,
    async_collection_tokio_add_python,
    sum_as_string_python,
)
from py03_benchmark.py03_benchmark import (
    async_collection_add,
    async_collection_tokio_add,
    sum_as_string,
)


async def async_rust(calls: int, size: int):
    l = [(i, i + 1) for i in range(size)]
    for i in range(calls):
        results = await async_collection_add(l)
    return


async def async_python(calls: int, size: int):
    l = [(i, i + 1) for i in range(size)]
    for i in range(calls):
        results = await async_collection_add_python(l)
    return


async def tokio_rust(calls: int, size: int):
    l = [(i, i + 1) for i in range(size)]
    for i in range(calls):
        results = await async_collection_tokio_add(l)
    return


async def tokio_python(calls: int, size: int):
    l = [(i, i + 1) for i in range(size)]
    for i in range(calls):
        results = await async_collection_tokio_add_python(l)
    return


async def measure(calls: int, size: int, rust_function, python_function, type: str):
    start = time.perf_counter()
    _ = await rust_function(calls, size)
    rust_time = time.perf_counter() - start

    print(
        f"{type} Rust with {calls} calls and list size {size} took {rust_time:.6f} seconds"
    )

    start = time.perf_counter()
    _ = await python_function(calls, size)
    python_time = time.perf_counter() - start

    print(
        f"{type} Python with {calls} calls and list size {size} took {python_time:.6f} seconds"
    )

    return {
        "calls": calls,
        "size": size,
        "rust_time": rust_time,
        "python_time": python_time,
        "type": type,
    }

async def main():
    print("py03-benchmark")

    call_size_list_async = [
        (4000000, 1),
        (2500, 10000),
        (10, 2000000),
    ]

    results = []

    for calls, size in call_size_list_async:
        result = await measure(calls, size, async_rust, async_python, "Async")
        results.append(result)

    call_size_list_tokio = [
        (1500000, 1),
        (2500, 3000),
        (5, 2000000),
    ]

    for calls, size in call_size_list_tokio:
        result = await measure(calls, size, tokio_rust, tokio_python, "Tokio")
        results.append(result)


if __name__ == "__main__":
    asyncio.run(main())
