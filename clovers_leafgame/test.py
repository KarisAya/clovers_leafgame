import asyncio


async def asyncfunc():
    print("Hello World")


def func():
    asyncio.create_task(asyncfunc())


async def main():
    func()
    while True:
        await asyncio.sleep(1)


asyncio.run(main())
