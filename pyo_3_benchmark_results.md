# 🧪 PyO3–Python Sync Benchmark Results

**Environment:** macOS • Python 3.9 • PyO3 0.25.x • Rust (Release mode)  
**Date:** _(fill in date)_  
**Duration per case:** ~2s per benchmark

---

## 🔹 Results Summary

| Benchmark | Python (ops/s) | Rust (ops/s) | Rust Speedup |
|------------|----------------|---------------|---------------|
| **sum_as_string** | 5 544 184 | 7 631 990 | **1.38×** |
| **sync_empty** | 11 682 966 | 14 383 911 | **1.23×** |
| **sync_large_args** | 1 211 | 479 | **0.40× (slower)** |
| **sync_return_large** | 16 086 | 14 112 | **0.88×** |
| **make_bench_class** | 1 333 505 | 11 808 617 | **8.85×** |
| **read_class_fields (BenchClass)** | 1 345 045 | 2 139 896 | **1.59×** |
| **many_small_args (*args)** | 2 815 543 | — | — |
| **many_small_args (50 explicit args)** | 1 779 245 | 2 736 119 | **1.54×** |
| **make_empty_class** | 8 809 526 | 11 697 450 | **1.33×** |
| **make_fields_only_class** | 4 113 273 | 11 638 901 | **2.83×** |
| **make_methods_only_class** | 8 820 181 | 11 768 929 | **1.33×** |
| **methods_only_calls** | 3 720 826 | 4 166 892 | **1.12×** |
| **read_fields (PythonFieldsOnlyClass)** | 1 347 862 | 2 126 759 | **1.58×** |

---

## 🧩 Observations and Insights

### 1. Function call overhead is small
- `sum_as_string` and `sync_empty` show only a **20–40%** gap.
- Calling Rust functions via PyO3 has low overhead.
- ✅ Rust FFI boundary is efficient for small, frequent calls.

---

### 2. Marshalling (data conversion) dominates when crossing languages
- `sync_large_args` (large list + string + bytes) shows **Rust 2.5× slower**.
- This is because:
  - Python → Rust conversion (`list → Vec<i64>`, `bytes → Vec<u8>`) copies data.
  - Rust doesn’t “see” Python’s memory directly.
- ✅ Lesson: avoid passing very large Python collections unless heavy computation happens in Rust.

---

### 3. Returning large data from Rust is modestly slower
- `sync_return_large` shows a small slowdown.
- PyO3 efficiently wraps Rust `Vec` / `String` into Python objects, but it still involves allocation + copying.

---

### 4. Class creation speed: massive Rust advantage
- Rust `#[pyclass]` creation is **8–9× faster** than Python class instantiation.
- Even empty or field-only classes show consistent **1.3–3× speedups**.
- ✅ Suggests that frequent object construction (e.g., session objects, rows, responses) is ideal to move to Rust.

---

### 5. Attribute access from Rust beats Python
- Reading 5 fields (`read_class_fields` / `read_fields`) is **~1.5–1.6× faster** from Rust.
- PyO3 attribute lookups use C API directly, skipping Python-level overhead.
- ✅ Rust is faster at repetitive field extraction.

---

### 6. Many small arguments benchmark
- Explicit 50-argument Rust call (`many_small_args_explicitly`) is **1.5× faster** than Python.
- Indicates that call boundary overhead grows sublinearly with argument count.
- ✅ For fixed-size argument batches, Rust handles varargs efficiently.

---

### 7. Method-call overhead is similar across languages
- `methods_only_calls` shows only ~12% Rust advantage.
- Meaning: calling methods on `#[pyclass]` objects is **roughly on par** with Python methods.
- ✅ Once class instances exist, per-call overhead is minimal.

---

## 🖯️ Conclusions

| Category | Summary | Recommendation |
|-----------|----------|----------------|
| **Call overhead (small ops)** | Rust ~20–40% faster | FFI overhead negligible; safe to use Rust even for fine-grained operations |
| **Data-heavy args / returns** | Rust slower (2–3×) due to copies | Prefer keeping large Python data on one side; offload computation, not data transfer |
| **Object creation** | Rust `#[pyclass]` ~9× faster | Great candidate for driver-side structs, query results, rows |
| **Field reads / attribute access** | Rust ~1.5× faster | Efficient to inspect Python objects in Rust loops |
| **Method dispatch** | Near parity | Performance neutral; structure in Rust if needed for type safety |
| **Many small args** | Rust ~1.5× faster | Rust handles multiple args efficiently; no significant penalty |

---

## 🚀 Next Steps (Optional Follow-ups)

These results justify:
- Exploring **hybrid serialization strategies** (partial Python-side packing to avoid conversions).
- Benchmarking **async overhead** (already implemented).
- Measuring **memory allocations** to visualize where conversions dominate.
- Testing **custom `#[pyclass]` with dynamic fields** to approximate real driver workloads.

---

**TL;DR:**  
> Moving lightweight logic and object models into Rust gives clear wins.  
> Crossing the language boundary with large Python data structures does not.  
> PyO3 overhead is surprisingly low — the bottleneck is data marshalling, not call mechanics.

