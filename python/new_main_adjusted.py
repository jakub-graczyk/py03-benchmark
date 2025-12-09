#!/usr/bin/env python3
"""
PyO3 / Python ↔ Rust benchmark harness.

This script is intended for use in experimental evaluation in a dissertation.
It:
- runs multiple trials per benchmark,
- reports per-trial ops/s,
- aggregates results (mean, std, min, max),
- can optionally export results to CSV for further analysis.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from new_lib import (
    empty_python,
    small_args_python,
    small_ret_args_python,
    make_empty_class_python,
    OneFieldClass,
    make_one_field_class_python,
    read_python,
    pass_obj_python,
    read_list_python,
    marshall_large_args_python,
    marshall_large_args_rust,
    marshall_large_return_python,
    marshall_large_return_rust,
    make_marshall_args_payload,
    MARSHALL_RETURN_LEN,
)
from py03_benchmark.py03_benchmark import (
    empty_rust,
    small_args_rust,
    small_ret_args_rust,
    make_empty_class_rust,
    make_one_field_class_rust,
    read_rust,
    read_list_rust,
    pass_obj_rust,
)


BenchmarkFn = Callable[[], None]


@dataclass
class TrialResult:
    label: str
    trial_index: int
    duration_s: float
    iterations: int
    ops_per_sec: float


@dataclass
class AggregateResult:
    label: str
    trials: int
    mean_ops: float
    std_ops: float
    min_ops: float
    max_ops: float


def bench_once(fn: BenchmarkFn, duration: float) -> TrialResult:
    """
    Run a single benchmark trial for approximately `duration` seconds.
    Returns a TrialResult with ops/s for this run.
    """
    start = time.perf_counter()
    iters = 0
    # Tight loop on the hot path
    while True:
        fn()
        iters += 1
        elapsed = time.perf_counter() - start
        if elapsed >= duration:
            break

    ops = iters / elapsed if elapsed > 0 else 0.0
    # label/trial_index are filled by the caller
    return TrialResult(label="", trial_index=-1, duration_s=elapsed, iterations=iters, ops_per_sec=ops)


def bench(
    fn: BenchmarkFn,
    label: str,
    duration: float,
    trials: int,
    all_results: List[TrialResult],
) -> None:
    """
    Run `trials` independent runs of `fn`, each for ~`duration` seconds.
    Stores per-trial results into `all_results`.
    """
    print(f"\n=== Benchmark: {label} (duration={duration:.2f}s, trials={trials}) ===")
    for i in range(trials):
        result = bench_once(fn, duration)
        result.label = label
        result.trial_index = i
        all_results.append(result)
        print(
            f"  trial {i:02d}: "
            f"{result.ops_per_sec:,.2f} ops/s "
            f"({result.iterations} iterations in {result.duration_s:.3f}s)"
        )


def aggregate_results(results: List[TrialResult]) -> List[AggregateResult]:
    """
    Group results by label and compute basic statistics.
    """
    by_label: Dict[str, List[TrialResult]] = {}
    for r in results:
        by_label.setdefault(r.label, []).append(r)

    aggregates: List[AggregateResult] = []
    for label, trials in sorted(by_label.items(), key=lambda kv: kv[0]):
        ops_values = [t.ops_per_sec for t in trials]
        mean_ops = statistics.fmean(ops_values)
        std_ops = statistics.pstdev(ops_values) if len(ops_values) > 1 else 0.0
        min_ops = min(ops_values)
        max_ops = max(ops_values)
        aggregates.append(
            AggregateResult(
                label=label,
                trials=len(trials),
                mean_ops=mean_ops,
                std_ops=std_ops,
                min_ops=min_ops,
                max_ops=max_ops,
            )
        )
    return aggregates


def print_summary_table(aggregates: List[AggregateResult]) -> None:
    """
    Print a human-readable summary table (good for logs / inspection).
    """
    print("\n================ Summary (ops/s) ================")
    header = f"{'Benchmark':35} {'trials':>6} {'mean':>15} {'std':>15} {'min':>15} {'max':>15}"
    print(header)
    print("-" * len(header))
    for agg in aggregates:
        print(
            f"{agg.label:35} "
            f"{agg.trials:6d} "
            f"{agg.mean_ops:15.2f} "
            f"{agg.std_ops:15.2f} "
            f"{agg.min_ops:15.2f} "
            f"{agg.max_ops:15.2f}"
        )


def write_csv(results: List[TrialResult], path: str) -> None:
    """
    Write raw per-trial results to CSV for analysis in R/NumPy/etc.
    Columns: label, trial_index, duration_s, iterations, ops_per_sec.
    """
    fieldnames = ["label", "trial_index", "duration_s", "iterations", "ops_per_sec"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "label": r.label,
                    "trial_index": r.trial_index,
                    "duration_s": f"{r.duration_s:.9f}",
                    "iterations": r.iterations,
                    "ops_per_sec": f"{r.ops_per_sec:.9f}",
                }
            )
    print(f"\n[info] Wrote CSV with {len(results)} trial rows to: {path}")


# --- Individual benchmark definitions --------------------------------------


def bench_empty(duration: float, trials: int, results: List[TrialResult]) -> None:
    bench(empty_python, "empty_python", duration, trials, results)
    bench(empty_rust, "empty_rust", duration, trials, results)


def bench_small_args(duration: float, trials: int, results: List[TrialResult]) -> None:
    def py():
        small_args_python(1, 2, 3, 4, 5)

    def rs():
        small_args_rust(1, 2, 3, 4, 5)

    bench(py, "small_args_python", duration, trials, results)
    bench(rs, "small_args_rust", duration, trials, results)


def bench_small_ret(duration: float, trials: int, results: List[TrialResult]) -> None:
    def py():
        _ = small_ret_args_python()

    def rs():
        _ = small_ret_args_rust()

    bench(py, "small_ret_args_python", duration, trials, results)
    bench(rs, "small_ret_args_rust", duration, trials, results)


def bench_make_empty_class(duration: float, trials: int, results: List[TrialResult]) -> None:
    bench(make_empty_class_python, "make_empty_class_python", duration, trials, results)
    bench(make_empty_class_rust, "make_empty_class_rust", duration, trials, results)


def bench_make_one_field_class(duration: float, trials: int, results: List[TrialResult]) -> None:
    bench(make_one_field_class_python, "make_one_field_class_python", duration, trials, results)
    bench(make_one_field_class_rust, "make_one_field_class_rust", duration, trials, results)

def bench_read_one_field(duration: float, trials: int, results: List[TrialResult]) -> None:
    obj = OneFieldClass()

    def py():
        read_python(obj)

    def rs():
        read_rust(obj)

    bench(py, "read_one_field_python", duration, trials, results)
    bench(rs, "read_one_field_rust", duration, trials, results)


def bench_pass_obj(duration: float, trials: int, results: List[TrialResult]) -> None:
    obj = OneFieldClass()

    def py():
        pass_obj_python(obj)

    def rs():
        pass_obj_rust(obj)

    bench(py, "pass_obj_python", duration, trials, results)
    bench(rs, "pass_obj_rust", duration, trials, results)


def bench_read_list(duration: float, trials: int, results: List[TrialResult]) -> None:
    lst = list(range(1000))

    def py():
        read_list_python(lst)

    def rs():
        read_list_rust(lst)

    bench(py, "read_list_python", duration, trials, results)
    bench(rs, "read_list_rust", duration, trials, results)


def bench_marshall_large_args(duration: float, trials: int, results: List[TrialResult]) -> None:
    # create payload ONCE, outside of the benchmarked functions
    lst, s, b = make_marshall_args_payload()

    def py():
        marshall_large_args_python(lst, s, b)

    def rs():
        marshall_large_args_rust(lst, s, b)

    bench(py, "marshall_large_args_python", duration, trials, results)
    bench(rs, "marshall_large_args_rust", duration, trials, results)


def bench_marshall_large_return(duration: float, trials: int, results: List[TrialResult]) -> None:
    length = MARSHALL_RETURN_LEN

    def py():
        _ = marshall_large_return_python(length)

    def rs():
        _ = marshall_large_return_rust(length)

    bench(py, "marshall_large_return_python", duration, trials, results)
    bench(rs, "marshall_large_return_rust", duration, trials, results)


# --- CLI / main ------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PyO3 / Python↔Rust micro-benchmarks for dissertation experiments."
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=2.0,
        help="Target duration (in seconds) per trial (default: 2.0)",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=5,
        help="Number of trials per benchmark (default: 5)",
    )
    parser.add_argument(
        "--csv-out",
        type=str,
        default=None,
        help="Optional path to write raw per-trial results as CSV",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    duration: float = args.duration
    trials: int = args.trials
    csv_out: Optional[str] = args.csv_out

    print(f"[info] Running benchmarks with duration={duration:.2f}s, trials={trials}")

    results: List[TrialResult] = []

    print("\n--- PyO3 overhead benchmarks ---")
    bench_empty(duration, trials, results)
    bench_small_args(duration, trials, results)
    bench_small_ret(duration, trials, results)
    bench_make_empty_class(duration, trials, results)
    bench_read_one_field(duration, trials, results)
    bench_pass_obj(duration, trials, results)
    bench_make_one_field_class(duration, trials, results)

    print("\n--- Marshalling benchmarks ---")
    bench_read_list(duration, trials, results)
    bench_marshall_large_args(duration, trials, results)
    bench_marshall_large_return(duration, trials, results)

    aggregates = aggregate_results(results)
    print_summary_table(aggregates)

    if csv_out:
        write_csv(results, csv_out)


if __name__ == "__main__":
    main()
