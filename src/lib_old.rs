use futures::future;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyTuple};
use std::sync::LazyLock;
use tokio::runtime::Runtime;

pub static RUNTIME: LazyLock<Runtime> = LazyLock::new(|| Runtime::new().unwrap());

/// ASYNCHRONOUS FUNCTIONS

/// Asynchronous: sum pairs of integers in parallel using Tokio JoinSet.
#[pyfunction]
async fn async_collection_tokio_add(list: Vec<(i32, i32)>) -> Vec<i32> {
    let r = RUNTIME.spawn(async move {
        let mut joinset = tokio::task::JoinSet::new();
        for (a, b) in list {
            joinset.spawn(async move { async_add(a, b).await });
        }
        let results = joinset.join_all().await;
        results
    });
    r.await.unwrap()
}

/// Asynchronous: sum pairs of integers in parallel using futures::join_all.
#[pyfunction]
async fn async_collection_add(list: Vec<(i32, i32)>) -> Vec<i32> {
    let mut res = Vec::new();
    for (a, b) in list {
        let c = async_add(a, b);
        res.push(c);
    }
    let results = future::join_all(res).await;
    results
}

async fn async_add(a: i32, b: i32) -> i32 {
    let c = a + b;
    c
}

/// SYNCHRONOUS FUNCTIONS

/// Synchronous: do nothing. Used to measure pure call overhead.
#[pyfunction]
fn sync_empty() -> PyResult<()> {
    Ok(())
}

/// Synchronous: sum two usizes and return as String.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// Synchronous: accept large arguments and touch them minimally.
/// Python will pass: list[int], str, bytes.
#[pyfunction]
fn sync_large_args(list: Vec<i64>, s: &str, b: Vec<u8>) -> PyResult<i64> {
    let mut acc: i64 = 0;

    if !list.is_empty() {
        acc += list[0] + list[list.len() - 1];
    }

    if !s.is_empty() {
        let bytes = s.as_bytes();
        acc += bytes[0] as i64 + bytes[bytes.len() - 1] as i64;
    }

    if !b.is_empty() {
        acc += b[0] as i64 + b[b.len() - 1] as i64;
    }

    Ok(acc)
}

/// Synchronous: construct and return large list, str, bytes.
/// 'len' is controlled from Python so you can tune benchmark sizes.
#[pyfunction]
fn sync_return_large(len: usize) -> PyResult<(Vec<i64>, String, Vec<u8>)> {
    let list: Vec<i64> = (0..len as i64).collect();
    let s = "x".repeat(len);
    let bytes = vec![b'x'; len];

    Ok((list, s, bytes))
}

/// SYNCHRONOUS FUNCTIONS FOR BENCHMARKING METHOD AND FIELD ACCESS

// A simple benchmark class with 5 fields and 5 methods.
#[pyclass]
pub struct BenchClass {
    #[pyo3(get)]
    field_0: i64,
    #[pyo3(get)]
    field_1: i64,
    #[pyo3(get)]
    field_2: i64,
    #[pyo3(get)]
    field_3: i64,
    #[pyo3(get)]
    field_4: i64,
}

#[pymethods]
impl BenchClass {
    #[new]
    fn new() -> Self {
        BenchClass {
            field_0: 1,
            field_1: 2,
            field_2: 3,
            field_3: 4,
            field_4: 5,
        }
    }

    fn method_0(&self) -> i64 {
        self.field_0
    }

    fn method_1(&self) -> i64 {
        self.field_1
    }

    fn method_2(&self) -> i64 {
        self.field_2
    }

    fn method_3(&self) -> i64 {
        self.field_3
    }

    fn method_4(&self) -> i64 {
        self.field_4
    }
}

/// Create and return a BenchClass instance.
/// Used to measure overhead of creating a #[pyclass] object in Rust.
#[pyfunction]
fn make_bench_class() -> PyResult<BenchClass> {
    Ok(BenchClass::new())
}

/// Read multiple fields (field_0..field_4) from an arbitrary Python object.
///
/// This is intentionally generic (&PyAny) so we can pass:
/// - Rust BenchClass instances
/// - pure Python classes with matching attributes
#[pyfunction]
fn read_class_fields(obj: &Bound<'_, PyAny>) -> PyResult<i64> {
    let mut sum = 0i64;

    for i in 0..5 {
        let name = format!("field_{}", i);
        let value: i64 = obj.getattr(&name)?.extract()?;
        sum += value;
    }

    Ok(sum)
}

/// FUNCTIONS AND CLASSES FOR FOLLOW-UP BENCHMARKS

/// Variadic-style: many small integer arguments.
/// Python will call: many_small_args(1, 2, 3, ..., N)
#[pyfunction]
fn many_small_args(args: &Bound<'_, PyTuple>) -> PyResult<i64> {
    let mut sum = 0i64;

    for item in args.iter() {
        let v: i64 = item.extract()?;
        sum += v;
    }
    
    Ok(sum)
}

/// CAUTION: I wasn't able to make this function work with variable arguments,
/// so we have to explicitly define 50 arguments here.
/// 
/// Explicit: many small integer arguments.
/// Python will call: many_small_args_explicitly(1, 2, 3, ..., N)
#[pyfunction]
fn many_small_args_explicitly(arg0: i64, arg1: i64, arg2: i64, arg3: i64, arg4: i64,
                             arg5: i64, arg6: i64, arg7: i64, arg8: i64, arg9: i64,
                             arg10: i64, arg11: i64, arg12: i64, arg13: i64, arg14: i64,
                             arg15: i64, arg16: i64, arg17: i64, arg18: i64, arg19: i64,
                             arg20: i64, arg21: i64, arg22: i64, arg23: i64, arg24: i64,
                             arg25: i64, arg26: i64, arg27: i64, arg28: i64, arg29: i64,
                             arg30: i64, arg31: i64, arg32: i64, arg33: i64, arg34: i64,
                             arg35: i64, arg36: i64, arg37: i64, arg38: i64, arg39: i64,
                             arg40: i64, arg41: i64, arg42: i64, arg43: i64, arg44: i64,
                             arg45: i64, arg46: i64, arg47: i64, arg48: i64, arg49: i64) -> PyResult<i64> {
    Ok(arg0 + arg1 + arg2 + arg3 + arg4 +
       arg5 + arg6 + arg7 + arg8 + arg9 +
       arg10 + arg11 + arg12 + arg13 + arg14 +
       arg15 + arg16 + arg17 + arg18 + arg19 +
       arg20 + arg21 + arg22 + arg23 +arg24 +
      arg25 + arg26 + arg27 + arg28 +arg29 +
      arg30 + arg31 + arg32 + arg33 +arg34 +
      arg35 + arg36 + arg37 + arg38 +arg39 +
      arg40 + arg41 + arg42 + arg43 +arg44 +
      arg45 + arg46 + arg47 + arg48 +arg49)
}

#[pyclass]
pub struct EmptyClass;

#[pymethods]
impl EmptyClass {
    #[new]
    fn new() -> Self {
        EmptyClass
    }
}

/// Create and return an EmptyClass instance.
/// Followup: pure overhead of class creation without fields/methods.
#[pyfunction]
fn make_empty_class() -> PyResult<EmptyClass> {
    Ok(EmptyClass)
}

#[pyclass]
pub struct FieldsOnlyClass {
    #[pyo3(get)]
    field_0: i64,
    #[pyo3(get)]
    field_1: i64,
    #[pyo3(get)]
    field_2: i64,
    #[pyo3(get)]
    field_3: i64,
    #[pyo3(get)]
    field_4: i64,
}

#[pymethods]
impl FieldsOnlyClass {
    #[new]
    fn new() -> Self {
        FieldsOnlyClass {
            field_0: 1,
            field_1: 2,
            field_2: 3,
            field_3: 4,
            field_4: 5,
        }
    }
}

/// Create and return a FieldsOnlyClass instance.
#[pyfunction]
fn make_fields_only_class() -> PyResult<FieldsOnlyClass> {
    Ok(FieldsOnlyClass::new())
}

#[pyclass]
pub struct MethodsOnlyClass;

#[pymethods]
impl MethodsOnlyClass {
    #[new]
    fn new() -> Self {
        MethodsOnlyClass
    }

    fn method_0(&self) -> i64 { 1 }
    fn method_1(&self) -> i64 { 2 }
    fn method_2(&self) -> i64 { 3 }
    fn method_3(&self) -> i64 { 4 }
    fn method_4(&self) -> i64 { 5 }
}

/// Create and return a MethodsOnlyClass instance.
#[pyfunction]
fn make_methods_only_class() -> PyResult<MethodsOnlyClass> {
    Ok(MethodsOnlyClass)
}

/// A Python module implemented in Rust.
#[pymodule]
fn py03_benchmark(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Asynchronous functions
    m.add_function(wrap_pyfunction!(async_collection_add, m)?)?;
    m.add_function(wrap_pyfunction!(async_collection_tokio_add, m)?)?;
    
    // // Synchronous functions
    // m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    // m.add_function(wrap_pyfunction!(sync_empty, m)?)?;
    // m.add_function(wrap_pyfunction!(sync_large_args, m)?)?;
    // m.add_function(wrap_pyfunction!(sync_return_large, m)?)?;

    // // BenchClass and related functions
    // m.add_class::<BenchClass>()?;
    // m.add_function(wrap_pyfunction!(make_bench_class, m)?)?;
    // m.add_function(wrap_pyfunction!(read_class_fields, m)?)?;
    
    // // Follow-up benchmark functions
    // m.add_function(wrap_pyfunction!(many_small_args, m)?)?;
    // m.add_function(wrap_pyfunction!(many_small_args_explicitly, m)?)?;
    // m.add_class::<EmptyClass>()?;
    // m.add_class::<FieldsOnlyClass>()?;
    // m.add_class::<MethodsOnlyClass>()?;
    // m.add_function(wrap_pyfunction!(make_empty_class, m)?)?;
    // m.add_function(wrap_pyfunction!(make_fields_only_class, m)?)?;
    // m.add_function(wrap_pyfunction!(make_methods_only_class, m)?)?;
    
    Ok(())
}