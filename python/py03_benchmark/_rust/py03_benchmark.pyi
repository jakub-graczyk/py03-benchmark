def sum_as_string(a: int, b: int) -> str: ...
async def async_collection_add(list: list[tuple[int, int]]) -> None: ...
async def async_collection_tokio_add(list: list[tuple[int, int]]) -> None: ...
async def async_runtimes_add(list: list[tuple[int, int]]) -> None: ...
def sync_empty() -> None: ...
def sync_large_args(lst: list[int], s: str, b: bytes) -> int: ...
def sync_return_large(length: int) -> tuple[list[int], str, bytes]: ...

class BenchClass: ...

def make_bench_class() -> "BenchClass": ...
def read_class_fields(obj: "BenchClass") -> int: ...
def many_small_args(*args: int) -> int: ...
def many_small_args_explicitly(
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
) -> int: ...

class EmptyClass: ...

def make_empty_class() -> "EmptyClass": ...

class FieldsOnlyClass: ...

def make_fields_only_class() -> "FieldsOnlyClass": ...

class MethodsOnlyClass: ...

def make_methods_only_class() -> "MethodsOnlyClass": ...
