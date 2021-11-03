import asyncio


async def foo():
    print('will sleep now')
    await asyncio.sleep(10_000)
    print('woke up')


async def main():
    task: asyncio.Task = asyncio.create_task(foo())

    await asyncio.sleep(1)

    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        print('caught')


asyncio.run(main())
