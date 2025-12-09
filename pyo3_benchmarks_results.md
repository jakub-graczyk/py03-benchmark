# PyO3 Benchmark Summary

This document summarises the results of microbenchmarks comparing Python methods and Rust methods exported via PyO3 and imported by Python of various operations relevant to designing the Python Over Rust Driver.

Benchmarks were executed in Python for 5 trials, each running for a fixed time window, and throughput is reported in operations per second (ops/s) with mean, standard deviation, min and max.

Below is a simplified table focusing on readability.
Values are mean ops/s (higher = faster) and standard deviation.
For clarity, min/max are omitted here but available in the raw CSV.

---

## 1. Function Call Overhead (Small Scalar Arguments)

### 1.1. Empty function

These functions test **bare call overhead**.

Python: `def empty_python(): pass`

vs

Rust via PyO3: 
`fn empty_rust() -> PyResult<()> { Ok(())}`

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 12,523,526 | **289,903** |
| Rust via PyO3 | 15,377,957 | **8,394** |

### 1.2. Take small arguments

These functions take five integers, they measure **conviersion of Python ints to `i32` vs no conversion**.

Python: `def small_args_python(a, b, c, d, e): return None`

vs

Rust via PyO3: 
`fn small_args_rust(a: i32, b: i32, c: i32, d: i32, e: i32) -> PyResult<()> { Ok(()) }`

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 8,390,872 | **19,356** |
| Rust via PyO3 | 7,365,731 | **5,761** |

### 1.3. Return small arguments

These functions have 0 arguments, and return an int. They measure **conversion of one `i32` to Python vs no conversion**.

Python: `def small_ret_args_python(): return 123`

vs

Rust via PyO3: 
`fn small_ret_args_rust() -> PyResult<i32> { Ok(123) }`

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 8,744,104 | **14,658** |
| Rust via PyO3 | 9,829,456 | **219,897** |
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
| Python | 9,118,878 | **42,237** |
| Rust via PyO3 | 12,716,609 | **13,226** |

### 2.2. One-field class creation

These functions create and return a trivial object with a single integer field value = 1. They compare **Python class instantiation with creating a Rust #[pyclass] struct and wrapping it for Python**.

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 6,054,601 | **16,557** |
| Rust via PyO3 | 12,243,159 | **232,505** |

### 2.3. Reading from a one-field class object

In this case two symmetric functions take an already-constructed Python object with one field, perform one atribbute lookup (`obj.value` vs `obj.getattr("value")?.extract()?;`) and return `val + val + val`. In total **one lookup + 2 additions**.

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 7,208,074 | **19,936** |
| Rust via PyO3 | 6,708,967 | **26,834** |

### 2.4. Passing objects

These function compare **passing PyObject vs Borrowed PyAny across the boundary** and doing nothing.

Python: `def pass_obj_python(obj): return None`

vs

Rust via PyO3: 
`fn pass_obj_rust(obj: Bound<'_, PyAny>) -> PyResult<()> { Ok(()) }`

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 8,514,280 | **13,257** |
| Rust via PyO3 | 9,557,952 | **17,620** |

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
| Python | 6,684,852 | **16,690** |
| Rust via PyO3 | 8,642,140 | **6,980** |

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
| Python | 7,543,781 | **11045** |
| Rust via PyO3 | 784| **4** |

---

## 5. Marshalling Large Return Values (Rust → Python)

Functions with no arguments that create a long list, string, and sequence of bytes and return. They measure **the cost of creating big data + returning it to Python across the boundary vs native Python doing it all itself**.

| Benchmark | mean (ops/s) | std (ops/s) |
|----------|----------------|--------------|
| Python | 1,326 | **12** |
| Rust via PyO3 | 1,250 | **13** |

---

# Interpretation & Practical Conclusions for Driver Design

### 1. **PyO3 overhead for small values is negligible**

Function calls, small argument passing, small returns, and simple arithmetic all run in the 7–15M ops/s range on both sides. Crossing the Python ↔ Rust boundary is not a bottleneck for typical driver logic, such as:
- metadata parsing  
- query state-machine logic  
- error handling  
- protocol flag parsing  
- small message fields (ints, bools, timestamps)

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

Both Python and Rust achieve 6–8M ops/s for reading object fields or indexing lists.
PyO3’s overhead for reads is small and predictable.

---

### 4. **Passing Python objects into Rust is extremely cheap**

Passing a PyAny reference into Rust costs almost nothing (~9.5M ops/s).
You can freely pass:
- prepared statements
- metadata
- configs
- connection handles

without performance concerns.

---

### 5. **Python → Rust conversion of large data is tonly major slowdown**

Converting large lists and byte buffers into Rust drops to ~784 ops/s, because Rust must:
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

- small inputs (queries, parameters)  
- large outputs (rows, columns, buffers)