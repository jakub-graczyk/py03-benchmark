# Python vs Rust via PyO3 Benchmarks Description

This document summarizes the results of microbenchmarks comparing Python methods and Rust methods exported via PyO3 and imported by Python of various operations relevant to designing the Python Over Rust Driver.

Benchmarks were executed in Python for 5 trials, each running for a fixed time window, and throughput is reported in operations per second (ops/s) with mean, standard deviation, min and max.

Values are mean ops/s (higher = faster).

## Raw summary (ops/s)

| Benchmark                     | Trials | Mean (ops/s)    | Std        | Min           | Max           |
|------------------------------|--------|-----------------|------------|---------------|---------------|
| empty_python                 | 5      | 12,451,345.80   | 268,518.00 | 11,926,091.50 | 12,643,046.50 |
| empty_rust                   | 5      | 15,600,117.17   | 12,051.73  | 15,578,575.00 | 15,612,242.18 |
| make_empty_class_python      | 5      | 9,250,046.21    | 64,740.56  | 9,120,816.31  | 9,286,953.00  |
| make_empty_class_rust        | 5      | 12,912,827.29   | 17,435.19  | 12,881,664.73 | 12,933,570.50 |
| make_one_field_class_python  | 5      | 6,102,136.92    | 8,517.15   | 6,087,478.50  | 6,114,128.75  |
| make_one_field_class_rust    | 5      | 12,223,555.25   | 687,186.66 | 10,850,077.00 | 12,595,588.50 |
| marshall_large_args_python   | 5      | 7,781,971.84    | 56,606.47  | 7,681,356.00  | 7,833,345.00  |
| marshall_large_args_rust     | 5      | 823.78          | 8.22       | 814.27        | 834.29        |
| marshall_large_return_python | 5      | 1,316.00        | 12.69      | 1,291.09      | 1,324.77      |
| marshall_large_return_rust   | 5      | 1,253.30        | 4.72       | 1,243.94      | 1,256.52      |
| pass_obj_python              | 5      | 8,755,214.13    | 16,082.85  | 8,729,522.63  | 8,771,916.63  |
| pass_obj_rust                | 5      | 9,724,792.58    | 10,548.08  | 9,714,197.00  | 9,740,702.50  |
| read_list_python             | 5      | 6,665,568.48    | 97,126.74  | 6,483,304.73  | 6,738,689.72  |
| read_list_rust               | 5      | 8,834,119.02    | 10,489.96  | 8,819,491.63  | 8,845,387.63  |
| read_one_field_python        | 5      | 7,338,650.02    | 19,155.69  | 7,303,797.85  | 7,359,094.85  |
| read_one_field_rust          | 5      | 6,771,176.12    | 24,116.78  | 6,725,710.72  | 6,795,603.71  |
| small_args_python            | 5      | 8,472,708.39    | 12,264.90  | 8,458,804.32  | 8,494,233.83  |
| small_args_rust              | 5      | 7,646,674.67    | 21,860.42  | 7,613,209.50  | 7,671,917.00  |
| small_ret_args_python        | 5      | 8,940,156.29    | 14,045.01  | 8,916,666.50  | 8,957,617.81  |
| small_ret_args_rust          | 5      | 10,225,167.00   | 17,336.78  | 10,206,047.29 | 10,255,703.78 |


# Detailed Explanations Of Benchmarks


## 1. Function Call Overhead (Small Scalar Arguments)

### 1.1. Empty function

These functions test **bare call overhead**.

Python: `def empty_python(): pass`

vs

Rust via PyO3: 
`fn empty_rust() -> PyResult<()> { Ok(())}`

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 12,451,346 | **268,518** |
| Rust via PyO3 | 15,600,117 | **12,052** |

### 1.2. Take small arguments

These functions take five integers, they measure **conversion of Python ints to `i32` vs no conversion**.

Python: `def small_args_python(a, b, c, d, e): return None`

vs

Rust via PyO3: 
`fn small_args_rust(a: i32, b: i32, c: i32, d: i32, e: i32) -> PyResult<()> { Ok(()) }`

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 8,472,708 | **12,265** |
| Rust via PyO3 | 7,646,675 | **21,860** |

### 1.3. Return small arguments

These functions have 0 arguments, and return an int. They measure **conversion of one `i32` to Python vs no conversion**.

Python: `def small_ret_args_python(): return 123`

vs

Rust via PyO3: 
`fn small_ret_args_rust() -> PyResult<i32> { Ok(123) }`

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 8,940,156 | **14,045** |
| Rust via PyO3 | 10,225,167 | **17,337** |
---

## 2. Object Creation and Field Access

### 2.1. Empty class

Empty class is created and returned. **Python object creation vs Rust `#[pyclass]` creation and wrapping** is compared.

Python: `def make_empty_class_python(): return EmptyClass()`

vs

Rust via PyO3: 
`fn make_empty_class_rust() -> PyResult<EmptyClass> { Ok(EmptyClass) }`

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 9,250,046 | **64,741** |
| Rust via PyO3 | 12,912,827 | **17,435** |

### 2.2. One-field class creation

These functions create and return a trivial object with a single integer field value = 1. They compare **Python class instantiation with creating a Rust #[pyclass] struct and wrapping it for Python**.

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 6,102,137 | **8,517** |
| Rust via PyO3 | 12,223,555 | **687,187** |

### 2.3. Reading from a one-field class object

In this case two symmetric functions take an already-constructed Python object with one field, perform one atribbute lookup (`obj.value` vs `obj.getattr("value")?.extract()?;`) and return `val + val + val`. In total **one lookup + 2 additions**.

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 7,338,650 | **19,156** |
| Rust via PyO3 | 6,771,176 | **24,117** |

### 2.4. Passing objects

These function compare **passing PyObject vs Borrowed PyAny across the boundary** and doing nothing.

Python: `def pass_obj_python(obj): return None`

vs

Rust via PyO3: 
`fn pass_obj_rust(obj: Bound<'_, PyAny>) -> PyResult<()> { Ok(()) }`

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 8,755,214 | **16,083** |
| Rust via PyO3 | 9,724,793 | **10,548** |

---

## 3. List Access (1,000 elements)

Both sides operate on the same Python list of 1,000 integers, created once outside the benchmark loop. Each function:
- reads the first element (`lst[0]` on the Python side, `list.get_item(0)` on the Rust side)
- converts it to a native integer (automatic in Python, `extract::<i32>()` in Rust)
- returns `val + val + val.`

This measures: **Python’s cost of indexing + integer arithmetic
vs Rust via PyO3 doing a single list indexing operation plus one integer conversion and the same arithmetic**.

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 6,665,568 | **97,127** |
| Rust via PyO3 | 8,834,119 | **10,490** |

---

## 4. Marshalling Large Arguments (Python → Rust Conversion)

In these benchmarks, Python constructs a large payload once outside the timed loop:
- a list of MARSHALL_LIST_LEN integers,
- a string of length MARSHALL_STR_LEN,
- a bytes object of length MARSHALL_BYTES_LEN.

The Python version simply receives these objects and does nothing (just binds them to a local tuple), while the Rust version receives the same objects and converts them into native Rust types:
- Python list → `Vec<i32>` (copy + per-element conversion)
- Python string → `&str (borrow)`
- Python bytes → `Vec<u8> (copy)`

This benchmark is intentionally one-sided: it essentially **measures the upper bound on Python → Rust conversion cost for large containers**, since the Python baseline does almost no work.

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 7,781,972 | **56,606** |
| Rust via PyO3 | 824 | **8** |

---

## 5. Marshalling Large Return Values (Rust → Python)

Functions with no arguments that create a long list, string, and sequence of bytes and return. They measure **the cost of creating big data + returning it to Python across the boundary vs native Python doing it all itself**.

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 1,316 | **13** |
| Rust via PyO3 | 1,253 | **5** |

---

# Interpretation & Practical Conclusions for Driver Design

### 1. **PyO3 overhead for small values is negligible**

Function calls, small returns, and simple arithmetic are all faster in Rust. Only passing small arguments to a function is slightly slower using PyO3, but this is expected due to (minimal but present) integer conversion. Overall, PyO3 overhead for small values is no problem.

This is expected because PyO3 calls map almost directly onto CPython’s C API.

---

### 2. **Rust efficiently constructs Python objects**

Rust #[pyclass] instantiation is almost 2× faster than Python’s own class creation.
This makes Rust ideal for building:
- rows  
- columns
- metadata objects

---

### 3. **Attribute lookup and list indexing are efficient**

Both Python and Rust achieve 6.5–7.5M ops/s for reading object fields or indexing lists.
PyO3’s overhead for reads is small and negligible.

---

### 4. **Passing Python objects into Rust is extremely cheap**

Passing a PyAny reference into Rust costs almost nothing (~9.7M ops/s).
You can freely pass:
- prepared statements
- metadata
- connection handles

without performance concerns.

---

### 5. **Python → Rust conversion of large data is tonly major slowdown**

Converting large lists and byte buffers into Rust drops to ~824 ops/s, because Rust must:
- allocate new buffers
- copy all data
- validate element types

Driver implications:

- Avoid passing large Python lists or batches into Rust.  
- Prefer constructing large value buffers entirely in Rust.

---

### 6. **Rust → Python conversion is relatively inexpensive**

Returning large lists/strings/bytes from Rust achieves similar throughput to doing it in Python (~1200–1300 ops/s). 
This is ideal because DB drivers usually have:

- small inputs
- large outputs