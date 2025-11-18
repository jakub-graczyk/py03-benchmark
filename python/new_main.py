import time

from .new_lib import (
    empty_python,
    small_args_python,
    small_ret_args_python,
    make_empty_class_python,
    OneFieldClass,
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
    read_rust,
    read_list_rust,
    pass_obj_rust,
)


def bench(fn, label: str, duration: float = 2.0):
    start = time.perf_counter()
    iters = 0
    while time.perf_counter() - start < duration:
        fn()
        iters += 1
    elapsed = time.perf_counter() - start
    print(f"{label}: {iters / elapsed:.2f} ops/s")

def bench_empty():
    bench(empty_python, "empty_python")
    bench(empty_rust, "empty_rust")

def bench_small_args():
    def py():
        small_args_python(1, 2, 3, 4, 5)

    def rs():
        small_args_rust(1, 2, 3, 4, 5)

    bench(py, "small_args_python")
    bench(rs, "small_args_rust")

def bench_small_ret():
    def py():
        _ = small_ret_args_python()

    def rs():
        _ = small_ret_args_rust()

    bench(py, "small_ret_args_python")
    bench(rs, "small_ret_args_rust")

def bench_make_empty_class():
    bench(make_empty_class_python, "make_empty_class_python")
    bench(make_empty_class_rust, "make_empty_class_rust")

def bench_read_one_field():
    obj = OneFieldClass()

    def py():
        read_python(obj)

    def rs():
        read_rust(obj)

    bench(py, "read_one_field_python")
    bench(rs, "read_one_field_rust")


def bench_pass_obj():
    obj = OneFieldClass()

    def py():
        pass_obj_python(obj)

    def rs():
        pass_obj_rust(obj)

    bench(py, "pass_obj_python")
    bench(rs, "pass_obj_rust")

def bench_read_list():
    lst = list(range(1000))

    def py():
        read_list_python(lst)

    def rs():
        read_list_rust(lst)

    bench(py, "read_list_python")
    bench(rs, "read_list_rust")


def bench_marshall_large_args():
    # create payload ONCE, outside of the benchmarked functions
    lst, s, b = make_marshall_args_payload()

    def py():
        marshall_large_args_python(lst, s, b)

    def rs():
        marshall_large_args_rust(lst, s, b)

    bench(py, "marshall_large_args_python")
    bench(rs, "marshall_large_args_rust")


def bench_marshall_large_return():
    length = MARSHALL_RETURN_LEN

    def py():
        _ = marshall_large_return_python(length)

    def rs():
        _ = marshall_large_return_rust(length)

    bench(py, "marshall_large_return_python")
    bench(rs, "marshall_large_return_rust")


def main():
    print("--- PyO3 overhead benchmarks ---")
    bench_empty()
    bench_small_args()
    bench_small_ret()
    bench_make_empty_class()
    bench_read_one_field()
    bench_pass_obj()
    bench_read_list()
    print("--- Marshalling benchmarks ---")
    bench_marshall_large_args()
    bench_marshall_large_return()

if __name__ == "__main__":
    main()
