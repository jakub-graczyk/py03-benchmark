from py03_benchmark.py03_benchmark import (
    marshall_large_args,
    marshall_large_ret,
)


"""Pure PyO3 overhead benchmarks: synchronous functions and classes."""

def empty_python():
    """Python no-op for call overhead baseline."""
    pass

def small_args_python(a, b, c, d, e):
    """Python no-op for 5 int args conversion overhead baseline."""
    return None

def small_ret_args_python():
    """Python no-op for small return value conversion overhead baseline."""
    return 123

class EmptyClass:
    pass

def make_empty_class_python():
    """Create and return an instance of EmptyClass."""
    return EmptyClass()

class OneFieldClass:
    def __init__(self) -> None:
        self.value = 1

def read_python(obj):
    """Read the single field from the OneFieldClass instance."""
    return obj.value + obj.value + obj.value
    
def pass_obj_python(obj):
    """Pass a Python object and do nothing."""
    return None

def read_list_python(lst):
    """Read first element from a list."""
    return lst[0]


"""Marshalling-heavy benchmarks."""

MARSHALL_LIST_LEN = 1_000_00
MARSHALL_STR_LEN = 1_000_00
MARSHALL_BYTES_LEN = 1_000_00
MARSHALL_RETURN_LEN = 1_000_00

def make_marshall_args_payload():
    """Creates large list/str/bytes for marshalling benchmarks."""
    lst = list(range(MARSHALL_LIST_LEN))
    s = "x" * MARSHALL_STR_LEN
    b = b"x" * MARSHALL_BYTES_LEN
    return lst, s, b

def marshall_large_args_python(lst: list[int], s: str, b: bytes) -> None:
    """Python baseline: marshalling large list/str/bytes."""
    _ = lst, s, b
    return None


def marshall_large_args_rust(lst: list[int], s: str, b: bytes) -> None:
    """Call the Rust marshalling large args function."""
    marshall_large_args(lst, s, b)

def marshall_large_return_python(length: int):
    """Python: create large data and return it (list/str/bytes)."""
    lst = list(range(length))
    s = "x" * length
    b = b"x" * length
    return lst, s, b

def marshall_large_return_rust(length: int):
    """Rust: create large data and return it (list/str/bytes)."""
    return marshall_large_ret(length)
