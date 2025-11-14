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


# START GENAI
def create_graphs(results, output_dir="graphs"):
    """Generate Plotly graphs from benchmark results"""
    # Clear the output directory if it exists
    if Path(output_dir).exists():
        shutil.rmtree(output_dir)
        print(f"Cleared existing graphs directory: {output_dir}")
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Separate results by type (Async vs Tokio)
    async_results = [r for r in results if r["type"] == "Async"]
    tokio_results = [r for r in results if r["type"] == "Tokio"]

    # Generate graphs for each configuration
    for result_set, label in [(async_results, "Async"), (tokio_results, "Tokio")]:
        if not result_set:
            continue

        # Create individual graphs for each call size configuration
        for i, result in enumerate(result_set, 1):
            calls = result["calls"]
            size = result["size"]
            rust_time = result["rust_time"]
            python_time = result["python_time"]

            # Bar chart comparing Rust vs Python
            fig = go.Figure(
                data=[
                    go.Bar(
                        name="Rust",
                        x=["Implementation"],
                        y=[rust_time],
                        marker_color="#CE422B",
                    ),
                    go.Bar(
                        name="Python",
                        x=["Implementation"],
                        y=[python_time],
                        marker_color="#3776AB",
                    ),
                ]
            )

            fig.update_layout(
                title=f"{label} - {calls:,} calls × {size:,} list size",
                yaxis_title="Time (seconds)",
                xaxis_title="",
                barmode="group",
                template="plotly_white",
                showlegend=True,
                height=500,
                width=800,
            )

            filename = f"{output_dir}/{label.lower()}_calls{calls}_size{size}.html"
            fig.write_html(filename)
            print(f"Saved graph: {filename}")

            # Create speedup comparison
            speedup = python_time / rust_time if rust_time > 0 else 0

            fig2 = go.Figure(
                data=[
                    go.Bar(
                        x=["Speedup"],
                        y=[speedup],
                        marker_color="#4CAF50",
                        text=[f"{speedup:.2f}x"],
                        textposition="auto",
                    )
                ]
            )

            fig2.update_layout(
                title=f"{label} - Rust Speedup<br><sub>{calls:,} calls × {size:,} list size</sub>",
                yaxis_title="Speedup Factor (Python/Rust)",
                xaxis_title="",
                template="plotly_white",
                height=500,
                width=800,
            )

            filename = (
                f"{output_dir}/{label.lower()}_speedup_calls{calls}_size{size}.html"
            )
            fig2.write_html(filename)
            print(f"Saved graph: {filename}")

    # Create overview comparison graphs for each type
    for result_set, label in [(async_results, "Async"), (tokio_results, "Tokio")]:
        if not result_set:
            continue

        # Overview bar chart with all configurations
        labels_list = [f"{r['calls']:,} × {r['size']:,}" for r in result_set]
        rust_times = [r["rust_time"] for r in result_set]
        python_times = [r["python_time"] for r in result_set]

        fig = go.Figure(
            data=[
                go.Bar(
                    name="Rust", x=labels_list, y=rust_times, marker_color="#CE422B"
                ),
                go.Bar(
                    name="Python", x=labels_list, y=python_times, marker_color="#3776AB"
                ),
            ]
        )

        fig.update_layout(
            title=f"{label} - Performance Comparison Across All Configurations",
            xaxis_title="Calls × List Size",
            yaxis_title="Time (seconds)",
            barmode="group",
            template="plotly_white",
            height=600,
            width=1000,
        )

        filename = f"{output_dir}/{label.lower()}_overview.html"
        fig.write_html(filename)
        print(f"Saved graph: {filename}")

        # Speedup overview
        speedups = [
            python_times[i] / rust_times[i] if rust_times[i] > 0 else 0
            for i in range(len(rust_times))
        ]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=labels_list,
                    y=speedups,
                    marker_color="#4CAF50",
                    text=[f"{s:.2f}x" for s in speedups],
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title=f"{label} - Rust Speedup Overview",
            xaxis_title="Calls × List Size",
            yaxis_title="Speedup Factor (Python/Rust)",
            template="plotly_white",
            height=600,
            width=1000,
        )

        filename = f"{output_dir}/{label.lower()}_speedup_overview.html"
        fig.write_html(filename)
        print(f"Saved graph: {filename}")


# END GENAI


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

    print("Creating graphs to graph/")
    create_graphs(results)


if __name__ == "__main__":
    asyncio.run(main())
