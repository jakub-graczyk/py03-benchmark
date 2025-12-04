# PyO3 Async Runtime Benchmark

This branch benchmarks different approaches of integrating Rust async code using PyO3 with Python's asyncio.

## Overview

The benchmark compares three different implementations of the same async task:

1. **Tokio with Async Runtimes** - Rust implementation using `pyo3_async_runtimes::tokio::future_into_py` to bridge Tokio futures to Python's asyncio
2. **Tokio with PyO3** - Rust implementation using a static Tokio runtime with manual spawning
3. **Asyncio Python** - Pure Python implementation using asyncio

Each implementation spawns multiple concurrent tasks that perform simple integer addition, simulating some workload (sufficient to prevent optimization).

## Test Scenarios

The benchmark runs three distinct scenarios to test different usage patterns:

| Scenario | Calls | List Size | Total Operations |
|----------|-------|-----------|------------------|
| Many small tasks | 150,000 | 8 | 1,200,000 |
| Medium tasks | 2,500 | 1,000 | 2,500,000 |
| Few large tasks | 5 | 200,000 | 1,000,000 |

## Implementation Details

### Rust (PyO3 with Async Runtimes)

```
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
```


### Rust (PyO3 with Static Runtime)

```
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
```


### Python (Asyncio)

```
async def python_asyncio(list: list[tuple[int, int]]) -> None:
    # Simulate Joinset by creating tasks
    tasks = [asyncio.create_task(async_add(a, b)) for a, b in list]
    results = []

    # As soon as they complete await them and store result this aims to mimic .join_all().await
    for task in asyncio.as_completed(tasks):
        result = await task
        results.append(result)

```

## Benchmark Results

## Scenario 1: Many Small Tasks (150,000 calls × 8 items)

| Implementation                | Mean        | Std Dev     | vs Best        |
|------------------------------|-------------|-------------|----------------|
| **Asyncio Python**           | 16.291804s  | 0.996671s   | **Baseline**   |
| Tokio with Async Runtimes    | 16.773046s  | 0.438451s   | +2.96% slower  |
| Tokio with PyO3              | 23.554266s  | 0.255749s   | +44.6% slower  |

---

## Scenario 2: Medium Tasks (2,500 calls × 1,000 items)

| Implementation                | Mean        | Std Dev     | vs Best        |
|------------------------------|-------------|-------------|----------------|
| **Tokio with Async Runtimes**| 0.493685s   | 0.031063s   | **Baseline**   |
| Tokio with PyO3              | 0.563094s   | 0.020354s   | +14.1% slower  |
| Asyncio Python               | 17.919917s  | 1.223715s   | +3630% slower  |

---

## Scenario 3: Few Large Tasks (5 calls × 200,000 items)

| Implementation                | Mean        | Std Dev     | vs Best        |
|------------------------------|-------------|-------------|----------------|
| **Tokio with Async Runtimes**| 0.227458s   | 0.006903s   | **Baseline**   |
| Tokio with PyO3              | 0.254250s   | 0.008534s   | +11.8% slower  |
| Asyncio Python               | 6.655152s   | 0.573368s   | +2926% slower  |

## Conclusions

1. **Runtime Spawn**: In Scenario 1, the overhead of spawning tasks in Rust dominates, and all implementations perform similarly (Mainly due to GIL and OS thread (and by extension Tokio runtime in PyO3) interaction specific to CPython).

2. **Task Count**: When task count is moderate to low (Scenarios 2 & 3), Rust implementations are up to **~35x faster** than Python. In context of Python-Rust Driver this suggest it's better to limit amount of calls if possible and submit larger tasks.

3. **Python's Scaling Issue**: When we don't cross the language gap frequently, Rust outperforms Python significantly.
