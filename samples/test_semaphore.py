import asyncio

import pytest

pytestmark = pytest.mark.asyncio

counter = 0
sem = None


# TODO используя Semaphore избежать длительного сна
async def do_request():
    global counter, sem

    if sem is None:
        sem = asyncio.Semaphore(10)

    async with sem:
        counter += 1
        if counter > 5:
            await asyncio.sleep(10)
        await asyncio.sleep(0.1)
        counter -= 1


async def test():
    await asyncio.wait_for(
        asyncio.gather(*[do_request() for _ in range(10)]),
        timeout=1.2,
    )
