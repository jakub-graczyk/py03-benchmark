import asyncio
import os
import shutil
import time
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
from lib import (
    async_collection_add_python,
    async_collection_tokio_add_python,
)
from py03_benchmark.py03_benchmark import (
    async_collection_add,
    async_collection_tokio_add,
    async_runtimes_add,
)


async def async_rust(calls: int, size: int, l: list[tuple[int, int]]):
    tasks = [asyncio.create_task(async_collection_add(l)) for c in range(calls)]
    _ = await asyncio.gather(*tasks)
    return


async def async_python(calls: int, size: int, l: list[tuple[int, int]]):
    tasks = [asyncio.create_task(async_collection_add_python(l)) for c in range(calls)]
    _ = await asyncio.gather(*tasks)
    return


async def tokio_rust(calls: int, size: int, l: list[tuple[int, int]]):
    tasks = [asyncio.create_task(async_collection_tokio_add(l)) for c in range(calls)]
    _ = await asyncio.gather(*tasks)
    return


async def tokio_python(calls: int, size: int, l: list[tuple[int, int]]):
    tasks = [
        asyncio.create_task(async_collection_tokio_add_python(l)) for c in range(calls)
    ]
    _ = await asyncio.gather(*tasks)
    return


async def async_runtimes(calls: int, size: int, l: list[tuple[int, int]]):
    tasks = [async_runtimes_add(l) for c in range(calls)]
    _ = await asyncio.gather(*tasks)
    return


async def measure(calls: int, size: int, function, type: str, lang: str):
    l = [(i, i + 1) for i in range(size)]
    start = time.perf_counter()
    _ = await function(calls, size, l)
    execute_time = time.perf_counter() - start

    print(
        f"{type} {lang} with {calls} calls and list size {size} took {execute_time:.6f} seconds"
    )

    return {
        "calls": calls,
        "size": size,
        "time": execute_time,
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

    # Separate results by type (Async vs Tokio vs Async Runtimes)
    async_results = [r for r in results if r["type"] == "Async"]
    tokio_results = [r for r in results if r["type"] == "Tokio"]
    async_runtimes_results = [r for r in results if r["type"] == "Async Runtimes Tokio"]

    # Generate graphs for each configuration
    for result_set, label in [
        (async_results, "Async"),
        (tokio_results, "Tokio"),
        (async_runtimes_results, "Async Runtimes Tokio"),
    ]:
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

            # Create safe filename
            safe_label = label.lower().replace(" ", "_")
            filename = f"{output_dir}/{safe_label}_calls{calls}_size{size}.html"
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

            filename = f"{output_dir}/{safe_label}_speedup_calls{calls}_size{size}.html"
            fig2.write_html(filename)
            print(f"Saved graph: {filename}")

    # Create overview comparison graphs for each type
    for result_set, label in [
        (async_results, "Async"),
        (tokio_results, "Tokio"),
        (async_runtimes_results, "Async Runtimes Tokio"),
    ]:
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

        # Create safe filename
        safe_label = label.lower().replace(" ", "_")
        filename = f"{output_dir}/{safe_label}_overview.html"
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

        filename = f"{output_dir}/{safe_label}_speedup_overview.html"
        fig.write_html(filename)
        print(f"Saved graph: {filename}")

    # Create Tokio comparison graphs (Async Runtimes vs Classic Tokio)
    if tokio_results and async_runtimes_results:
        print("\nGenerating Tokio implementation comparison graphs...")

        # Match results by calls and size
        matched_pairs = []
        for tokio_result in tokio_results:
            for arr_result in async_runtimes_results:
                if (
                    tokio_result["calls"] == arr_result["calls"]
                    and tokio_result["size"] == arr_result["size"]
                ):
                    matched_pairs.append(
                        {
                            "calls": tokio_result["calls"],
                            "size": tokio_result["size"],
                            "tokio_time": tokio_result["rust_time"],
                            "async_runtimes_time": arr_result["rust_time"],
                            "python_time": tokio_result["python_time"],
                        }
                    )
                    break

        # Individual comparison graphs
        for pair in matched_pairs:
            calls = pair["calls"]
            size = pair["size"]
            tokio_time = pair["tokio_time"]
            arr_time = pair["async_runtimes_time"]
            python_time = pair["python_time"]

            # Three-way comparison
            fig = go.Figure(
                data=[
                    go.Bar(
                        name="Tokio",
                        x=["Implementation"],
                        y=[tokio_time],
                        marker_color="#CE422B",
                    ),
                    go.Bar(
                        name="Async Runtimes",
                        x=["Implementation"],
                        y=[arr_time],
                        marker_color="#FF6B35",
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
                title=f"Tokio Implementation Comparison<br><sub>{calls:,} calls × {size:,} list size</sub>",
                yaxis_title="Time (seconds)",
                xaxis_title="",
                barmode="group",
                template="plotly_white",
                showlegend=True,
                height=500,
                width=800,
            )

            filename = f"{output_dir}/tokio_comparison_calls{calls}_size{size}.html"
            fig.write_html(filename)
            print(f"Saved graph: {filename}")

            # Relative performance (which Tokio is faster)
            ratio = tokio_time / arr_time if arr_time > 0 else 0
            faster_impl = "Async Runtimes" if ratio > 1 else "Classic Tokio"
            speedup_factor = max(ratio, 1 / ratio) if ratio > 0 else 0

            fig2 = go.Figure(
                data=[
                    go.Bar(
                        name="Classic Tokio",
                        x=["Classic Tokio"],
                        y=[tokio_time],
                        marker_color="#CE422B",
                        text=[f"{tokio_time:.6f}s"],
                        textposition="auto",
                    ),
                    go.Bar(
                        name="Async Runtimes",
                        x=["Async Runtimes"],
                        y=[arr_time],
                        marker_color="#FF6B35",
                        text=[f"{arr_time:.6f}s"],
                        textposition="auto",
                    ),
                ]
            )

            fig2.update_layout(
                title=f"Tokio Implementations Side-by-Side<br><sub>{calls:,} calls × {size:,} list size | {faster_impl} is {speedup_factor:.2f}x faster</sub>",
                yaxis_title="Time (seconds)",
                xaxis_title="Implementation",
                template="plotly_white",
                showlegend=False,
                height=500,
                width=800,
            )

            filename = f"{output_dir}/tokio_sidebyside_calls{calls}_size{size}.html"
            fig2.write_html(filename)
            print(f"Saved graph: {filename}")

        # Overview comparison if we have multiple configurations
        if len(matched_pairs) > 0:
            labels_list = [f"{p['calls']:,} × {p['size']:,}" for p in matched_pairs]
            tokio_times = [p["tokio_time"] for p in matched_pairs]
            arr_times = [p["async_runtimes_time"] for p in matched_pairs]
            python_times = [p["python_time"] for p in matched_pairs]

            fig = go.Figure(
                data=[
                    go.Bar(
                        name="Classic Tokio",
                        x=labels_list,
                        y=tokio_times,
                        marker_color="#CE422B",
                    ),
                    go.Bar(
                        name="Async Runtimes",
                        x=labels_list,
                        y=arr_times,
                        marker_color="#FF6B35",
                    ),
                    go.Bar(
                        name="Python",
                        x=labels_list,
                        y=python_times,
                        marker_color="#3776AB",
                    ),
                ]
            )

            fig.update_layout(
                title="Tokio Implementation Comparison Overview",
                xaxis_title="Calls × List Size",
                yaxis_title="Time (seconds)",
                barmode="group",
                template="plotly_white",
                height=600,
                width=1000,
            )

            filename = f"{output_dir}/tokio_comparison_overview.html"
            fig.write_html(filename)
            print(f"Saved graph: {filename}")


# END GENAI


async def main():
    print("py03-benchmark")

    results = []

    call_size_list = [
        (150000, 1),
        (250, 300),
        (5, 20000),
    ]

    print("Tokio\n")
    print("For flamegraph leave function you want to measure and adjust call_size_list")
    for calls, size in call_size_list:
        arr = await measure(
            calls, size, async_runtimes, "Tokio with Async Runtimes", "Rust"
        )
        tr = await measure(calls, size, tokio_rust, "Tokio with PyO3", "Rust")
        tp = await measure(calls, size, tokio_python, "Asyncio", "Python")
        result1 = {
            "calls": calls,
            "size": size,
            "rust_time": tr["time"],
            "python_time": tp["time"],
            "type": tr["type"],
        }
        result2 = {
            "calls": calls,
            "size": size,
            "rust_time": arr["time"],
            "python_time": tp["time"],
            "type": arr["type"],
        }

        results.append(result1)
        results.append(result2)
        print("\n")

    # Uncomment for graphs
    # print("Creating graphs to graph/")
    # create_graphs(results)


if __name__ == "__main__":
    asyncio.run(main())
