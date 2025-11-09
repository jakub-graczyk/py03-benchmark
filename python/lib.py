import asyncio


def sum_as_string_python(a: int, b: int) -> str:
    return str(a + b)


async def async_collection_tokio_add_python(list: list[tuple[int, int]]) -> list[int]:
    # Simulate Joinset by creating tasks
    tasks = [asyncio.create_task(async_add(a, b)) for a, b in list]
    results = []

    # As soon as they complete await them and store result this aims to mimic .join_all().await
    for task in asyncio.as_completed(tasks):
        result = await task
        results.append(result)

    return results


async def async_collection_add_python(list: list[tuple[int, int]]) -> list[int]:
    res = []
    for a, b in list:
        c = async_add(a, b)
        res.append(c)
    results = await asyncio.gather(*res)
    return results


async def async_add(a: int, b: int) -> int:
    c = a + b
    return c
