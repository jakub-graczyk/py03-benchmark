use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3_async_runtimes;
use std::sync::LazyLock;
use tokio::runtime::Runtime;

pub static RUNTIME: LazyLock<Runtime> = LazyLock::new(|| Runtime::new().unwrap());

#[pyfunction]
async fn rust_tokio_with_pyo3(list: Vec<(i32, i32)>) {
    let r = RUNTIME.spawn(async move {
        let mut joinset = tokio::task::JoinSet::new();
        for (a, b) in list {
            joinset.spawn(async move { async_add(a, b).await });
        }
        let results = joinset.join_all().await;
        results
    });
    r.await.unwrap();
}

#[pyfunction]
fn rust_tokio_with_async_runtimes(py: Python, list: Vec<(i32, i32)>) -> PyResult<Bound<PyAny>> {
    pyo3_async_runtimes::tokio::future_into_py(py, async move {
        let mut joinset = tokio::task::JoinSet::new();
        for (a, b) in list {
            joinset.spawn(async move { async_add(a, b).await });
        }
        let _ = joinset.join_all().await;
        Ok(())
    })
}

async fn async_add(_a: i32, _b: i32) -> i32 {
    let c = _a + _b;
    return c;
}

/// A Python module implemented in Rust.
#[pymodule]
fn py03_benchmark(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rust_tokio_with_pyo3, m)?)?;
    m.add_function(wrap_pyfunction!(rust_tokio_with_async_runtimes, m)?)?;
    Ok(())
}
