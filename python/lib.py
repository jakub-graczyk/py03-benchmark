import asyncio

from py03_benchmark.py03_benchmark import (  # Rust module
    sync_large_args as sync_large_args_rust_helper,
)

## SYNC BASELINES

# Sizes for sync tests
LARGE_LIST_LEN = 100_000
LARGE_STR_LEN = 1_000_000
LARGE_BYTES_LEN = 100_000


def _make_large_list() -> list[int]:
    return list(range(LARGE_LIST_LEN))


def _make_large_str() -> str:
    return "x" * LARGE_STR_LEN


def _make_large_bytes() -> bytes:
    return b"x" * LARGE_BYTES_LEN


def sum_as_string_python(a: int, b: int) -> str:
    """Pure Python baseline matching the Rust sum_as_string."""
    return str(a + b)


def sync_empty_python() -> None:
    """Python no-op for call overhead baseline."""
    return None


def sync_large_args_python() -> int:
    """
    Pure Python: consume large list/str/bytes and return small int.
    Mirrors sync_large_args_rust semantics.
    """
    lst = _make_large_list()
    s = _make_large_str()
    b = _make_large_bytes()

    acc = 0
    if lst:
        acc += lst[0] + lst[-1]
    if s:
        acc += ord(s[0]) + ord(s[-1])
    if b:
        acc += b[0] + b[-1]
    return acc


def sync_return_large_python(length: int):
    """
    Pure Python: construct and return large list/str/bytes.
    Mirrors sync_return_large_rust.
    """
    vec = list(range(length))
    s = "x" * length
    b = b"x" * length
    return vec, s, b


# Rust wrapper
def sync_large_args_rust():
    lst = _make_large_list()
    s = _make_large_str()
    b = _make_large_bytes()
    return sync_large_args_rust_helper(lst, s, b)


## BENCH CLASS BASELINES
class PythonBenchClass:
    """
    Pure Python benchmark class mirroring RsBenchClass:
    5 fields (field_0..field_4) and 5 trivial methods.
    """

    def __init__(self):
        for i in range(5):
            setattr(self, f"field_{i}", i)

    def method_0(self) -> int:
        return 0

    def method_1(self) -> int:
        return 1

    def method_2(self) -> int:
        return 2

    def method_3(self) -> int:
        return 3

    def method_4(self) -> int:
        return 4


def make_python_bench_class() -> PythonBenchClass:
    return PythonBenchClass()


def read_class_fields_python(obj: PythonBenchClass) -> int:
    """Read and sum the 5 fields from a BenchClass instance."""
    sum = 0
    for i in range(5):
        sum += getattr(obj, f"field_{i}")
    return sum


## FOLLOW-UP BASELINES


def many_small_args_python(*args: int) -> int:
    return sum(args)


def many_small_args_explicitly_python(
    arg0: int,
    arg1: int,
    arg2: int,
    arg3: int,
    arg4: int,
    arg5: int,
    arg6: int,
    arg7: int,
    arg8: int,
    arg9: int,
    arg10: int,
    arg11: int,
    arg12: int,
    arg13: int,
    arg14: int,
    arg15: int,
    arg16: int,
    arg17: int,
    arg18: int,
    arg19: int,
    arg20: int,
    arg21: int,
    arg22: int,
    arg23: int,
    arg24: int,
    arg25: int,
    arg26: int,
    arg27: int,
    arg28: int,
    arg29: int,
    arg30: int,
    arg31: int,
    arg32: int,
    arg33: int,
    arg34: int,
    arg35: int,
    arg36: int,
    arg37: int,
    arg38: int,
    arg39: int,
    arg40: int,
    arg41: int,
    arg42: int,
    arg43: int,
    arg44: int,
    arg45: int,
    arg46: int,
    arg47: int,
    arg48: int,
    arg49: int,
) -> int:
    return (
        arg0
        + arg1
        + arg2
        + arg3
        + arg4
        + arg5
        + arg6
        + arg7
        + arg8
        + arg9
        + arg10
        + arg11
        + arg12
        + arg13
        + arg14
        + arg15
        + arg16
        + arg17
        + arg18
        + arg19
        + arg20
        + arg21
        + arg22
        + arg23
        + arg24
        + arg25
        + arg26
        + arg27
        + arg28
        + arg29
        + arg30
        + arg31
        + arg32
        + arg33
        + arg34
        + arg35
        + arg36
        + arg37
        + arg38
        + arg39
        + arg40
        + arg41
        + arg42
        + arg43
        + arg44
        + arg45
        + arg46
        + arg47
        + arg48
        + arg49
    )


class PythonEmptyClass:
    pass


class PythonFieldsOnlyClass:
    def __init__(self) -> None:
        self.field_0 = 1
        self.field_1 = 2
        self.field_2 = 3
        self.field_3 = 4
        self.field_4 = 5


class PythonMethodsOnlyClass:
    def method_0(self) -> int:
        return 1

    def method_1(self) -> int:
        return 2

    def method_2(self) -> int:
        return 3

    def method_3(self) -> int:
        return 4

    def method_4(self) -> int:
        return 5


def make_python_empty_class() -> PythonEmptyClass:
    return PythonEmptyClass()


def make_python_fields_only_class() -> PythonFieldsOnlyClass:
    return PythonFieldsOnlyClass()


def make_python_methods_only_class() -> PythonMethodsOnlyClass:
    return PythonMethodsOnlyClass()


## ASYNC BASELINES


async def async_collection_tokio_add_python(list: list[tuple[int, int]]) -> None:
    # Simulate Joinset by creating tasks
    tasks = [asyncio.create_task(async_add(a, b)) for a, b in list]
    results = []

    # As soon as they complete await them and store result this aims to mimic .join_all().await
    for task in asyncio.as_completed(tasks):
        result = await task
        results.append(result)


async def async_collection_add_python(list: list[tuple[int, int]]) -> None:
    res = []
    for a, b in list:
        c = async_add(a, b)
        res.append(c)
    _ = await asyncio.gather(*res)


async def async_add(a: int, b: int) -> None:
    pass
