import asyncio


async def task1():
    print("任务1开始")

    await asyncio.sleep(3)

    print("任务1结束")


async def task2():
    print("任务2开始")

    await asyncio.sleep(2)

    print("任务2结束")


async def main():
    await asyncio.gather(
        task1(),
        task2()
    )

asyncio.run(main())