import asyncio
from asyncio import Event, FIRST_COMPLETED
from typing import List, Coroutine

import pytest

pytestmark = pytest.mark.asyncio


# TODO реализовать функцию выполнения короутин
async def do_until_event(
        aws: List[Coroutine], event: asyncio.Event, timeout: float = None
):
    event.clear()

    pending = []
    while not event.is_set():
        _, pending = await asyncio.wait(fs=aws, timeout=timeout, return_when=FIRST_COMPLETED)

    for task in pending:
        task.cancel()


async def test():
    stop_event = Event()
    stop_event.set()

    async def set_event(event: Event):
        await asyncio.sleep(1)
        event.set()

    async def worker():
        while True:
            await asyncio.sleep(1)

    coros = [*[worker() for _ in range(10)], set_event(stop_event)]
    await asyncio.wait_for(
        do_until_event(coros, event=stop_event),
        timeout=1.2,
    )
