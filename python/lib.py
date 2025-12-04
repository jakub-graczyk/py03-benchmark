import asyncio


async def python_asyncio(list: list[tuple[int, int]]) -> None:
    # Simulate Joinset by creating tasks
    tasks = [asyncio.create_task(async_add(a, b)) for a, b in list]
    results = []

    # As soon as they complete await them and store result this aims to mimic .join_all().await
    for task in asyncio.as_completed(tasks):
        result = await task
        results.append(result)


async def async_add(a: int, b: int) -> int:
    c = a + b
    return c
