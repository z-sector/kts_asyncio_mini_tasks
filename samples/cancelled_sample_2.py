import asyncio


async def foo():
    try:
        print('will sleep now')
        await asyncio.sleep(10_000)
        print('woke up')
    except asyncio.CancelledError:
        print('caught')


async def main():
    task: asyncio.Task = asyncio.create_task(foo())

    await asyncio.sleep(1)

    task.cancel()

    await task


asyncio.run(main())
