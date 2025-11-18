use pyo3::prelude::*;
use pyo3::types::PyAny;


/// Pure PyO3 overhead benchmarks: synchronous functions and classes.

/// Do nothing.
#[pyfunction]
fn empty_rust() -> PyResult<()> {
    Ok(())
}

/// Accept small arguments and do nothing.
#[pyfunction]
fn small_args_rust (a: i32, b: i32, c: i32, d: i32, e: i32) -> PyResult<()> {
    Ok(())
}

/// Return small integer.
#[pyfunction]
fn small_ret_args_rust() -> PyResult<i32> {
    Ok(123)
}

#[pyclass]
pub struct EmptyClass;

/// Create and return an instance of EmptyClass.
#[pyfunction]
fn make_empty_class_rust() -> PyResult<EmptyClass> {
    Ok(EmptyClass)
}

/// Read 'value' attribute from a Python object three times, sum and return.
#[pyfunction]
fn read_rust(obj: Bound<'_, PyAny>) -> PyResult<i32> {
    let val: i32 = obj.getattr("value")?.extract()?;
    Ok(val + val + val)
}

/// Accept a Python object and do nothing.
#[pyfunction]
fn pass_obj_rust(obj: Bound<'_, PyAny>) -> PyResult<()> { Ok(()) }

/// Accept a list of u32 and return the first element.
#[pyfunction]
fn read_list_rust(lst: Vec<u32>) -> PyResult<u32> {
    Ok(lst[0])
}

/// Marshalling-heavy benchmarks.

/// Python passes large arguments: a list of integers, a string, and a bytes object to Rust.
#[pyfunction]
fn marshall_large_args(list: Vec<i32>, text: &str, b: Vec<u8>) -> PyResult<()> {
    let _ = (list, text, b);
    Ok(())
}

/// Rust creates large return values: a list of integers, a string, and a bytes object to Python.
#[pyfunction]
fn marshall_large_ret(len: usize) -> PyResult<(Vec<i32>, String, Vec<u8>)> {
    let list: Vec<i32> = (0..len as i32).collect();
    let text: String = "x".repeat(len);
    let bytes: Vec<u8> = vec![b'x'; len];
    Ok((list, text, bytes))
}

#[pymodule]
fn py03_benchmark(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // pyO3 overhead benchmarks
    m.add_function(wrap_pyfunction!(empty_rust, m)?)?;
    m.add_function(wrap_pyfunction!(small_args_rust, m)?)?;
    m.add_function(wrap_pyfunction!(small_ret_args_rust, m)?)?;
    m.add_function(wrap_pyfunction!(make_empty_class_rust, m)?)?;
    m.add_function(wrap_pyfunction!(read_rust, m)?)?;
    m.add_function(wrap_pyfunction!(pass_obj_rust, m)?)?;
    m.add_function(wrap_pyfunction!(read_list_rust, m)?)?;
    // marshalling benchmarks
    m.add_function(wrap_pyfunction!(marshall_large_args, m)?)?;
    m.add_function(wrap_pyfunction!(marshall_large_ret, m)?)?;
    Ok(())
}