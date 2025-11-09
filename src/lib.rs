use futures::future;
use pyo3::prelude::*;
use std::sync::LazyLock;
use tokio::runtime::Runtime;

pub static RUNTIME: LazyLock<Runtime> = LazyLock::new(|| Runtime::new().unwrap());

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b + 1000412000).to_string())
    // cach
}

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

/// A Python module implemented in Rust.
#[pymodule]
fn py03_benchmark(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    m.add_function(wrap_pyfunction!(async_collection_add, m)?)?;
    m.add_function(wrap_pyfunction!(async_collection_tokio_add, m)?)?;
    Ok(())
}
