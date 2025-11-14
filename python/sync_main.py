import time

from py03_benchmark.py03_benchmark import (
    make_bench_class as make_rust_bench_class,
)
from py03_benchmark.py03_benchmark import (
    make_empty_class as make_rust_empty_class,
)
from py03_benchmark.py03_benchmark import (
    make_fields_only_class as make_rust_fields_only_class,
)
from py03_benchmark.py03_benchmark import (
    make_methods_only_class as make_rust_methods_only_class,
)
from py03_benchmark.py03_benchmark import (
    many_small_args as many_small_args_rust,
)
from py03_benchmark.py03_benchmark import (
    many_small_args_explicitly as many_small_args_explicitly_rust,
)
from py03_benchmark.py03_benchmark import (
    read_class_fields as read_class_fields_rust,
)
from py03_benchmark.py03_benchmark import (
    sum_as_string as sum_as_string_rust,
)
from py03_benchmark.py03_benchmark import (
    sync_empty as sync_empty_rust,
)
from py03_benchmark.py03_benchmark import (
    sync_return_large as sync_return_large_rust,
)

from .lib import (
    PythonBenchClass,
    PythonFieldsOnlyClass,
    PythonMethodsOnlyClass,
    make_python_bench_class,
    make_python_empty_class,
    make_python_fields_only_class,
    make_python_methods_only_class,
    many_small_args_explicitly_python,
    many_small_args_python,
    read_class_fields_python,
    sum_as_string_python,
    sync_empty_python,
    sync_large_args_python,
    sync_large_args_rust,
    sync_return_large_python,
)


def bench(fn, label: str, duration: float = 2.0):
    start = time.perf_counter()
    iters = 0
    while time.perf_counter() - start < duration:
        fn()
        iters += 1
    elapsed = time.perf_counter() - start
    print(f"{label}: {iters / elapsed:.2f} ops/s")


def bench_sum_as_string():
    def py():
        sum_as_string_python(1, 2)

    def rs():
        sum_as_string_rust(1, 2)

    bench(py, "sum_as_string_python")
    bench(rs, "sum_as_string_rust")


def bench_sync_empty():
    bench(sync_empty_python, "sync_empty_python")
    bench(sync_empty_rust, "sync_empty_rust")


def bench_sync_large_args():
    bench(sync_large_args_python, "sync_large_args_python")
    bench(sync_large_args_rust, "sync_large_args_rust")


def bench_sync_return_large():
    def py():
        sync_return_large_python(10_000)

    def rs():
        sync_return_large_rust(10_000)

    bench(py, "sync_return_large_python")
    bench(rs, "sync_return_large_rust")


def bench_bench_class():
    bench(make_python_bench_class, "make_python_bench_class")
    bench(make_rust_bench_class, "make_rust_bench_class")


def bench_read_bench_class_fields():
    obj = PythonBenchClass()

    def py():
        read_class_fields_python(obj)

    def rs():
        read_class_fields_rust(obj)

    bench(py, "read_class_fields_python(BenchClass)")
    bench(rs, "read_class_fields_rust(BenchClass)")


def bench_many_small_args():
    # 50 small ints
    args = tuple(range(50))

    def py():
        many_small_args_python(*args)

    def rs():
        many_small_args_rust(*args)

    bench(py, "many_small_args_python")
    bench(rs, "many_small_args_rust")


def bench_many_small_args_explicitly():
    # 50 small ints
    args = tuple(range(50))

    def py():
        many_small_args_python(*args)

    def py_explicitly():
        many_small_args_explicitly_python(*args)

    def rs():
        many_small_args_explicitly_rust(*args)

    bench(py, "many_small_args_python")
    bench(py_explicitly, "many_small_args_explicitly_python")
    bench(rs, "many_small_args_explicitly_rust")


def bench_make_class_empty():
    bench(make_python_empty_class, "make_python_empty_class")
    bench(make_rust_empty_class, "make_rust_empty_class")


def bench_make_class_fields_only():
    bench(make_python_fields_only_class, "make_python_fields_only_class")
    bench(make_rust_fields_only_class, "make_rust_fields_only_class")


def bench_make_class_methods_only():
    bench(make_python_methods_only_class, "make_python_methods_only_class")
    bench(make_rust_methods_only_class, "make_rust_methods_only_class")


def bench_methods_only_calls():
    py_obj = PythonMethodsOnlyClass()
    rs_obj = make_rust_methods_only_class()

    def py():
        # call all 5 methods
        _ = (
            py_obj.method_0()
            + py_obj.method_1()
            + py_obj.method_2()
            + py_obj.method_3()
            + py_obj.method_4()
        )

    def rs():
        _ = (
            rs_obj.method_0()
            + rs_obj.method_1()
            + rs_obj.method_2()
            + rs_obj.method_3()
            + rs_obj.method_4()
        )

    bench(py, "methods_only_calls_python")
    bench(rs, "methods_only_calls_rust")


def bench_read_fields_only_class_fields():
    obj = PythonFieldsOnlyClass()

    def py():
        read_class_fields_python(obj)

    def rs():
        read_class_fields_rust(obj)

    bench(py, "read_fields_python(PythonFieldsOnlyClass)")
    bench(rs, "read_fields_rust(PythonFieldsOnlyClass)")


def main():
    print("--- Sync benchmarks ---")
    bench_sum_as_string()
    bench_sync_empty()
    bench_sync_large_args()
    bench_sync_return_large()
    bench_bench_class()
    bench_read_bench_class_fields()
    # bench_many_small_args()
    bench_many_small_args_explicitly()
    bench_make_class_empty()
    bench_make_class_fields_only()
    bench_make_class_methods_only()
    bench_methods_only_calls()
    bench_read_fields_only_class_fields()


if __name__ == "__main__":
    main()
