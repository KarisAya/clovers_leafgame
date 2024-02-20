import asyncio
import timeit

itr = (i for i in range(500))
ist = [x for x in itr]
time_taken = timeit.timeit(lambda: list(itr), number=10000)
print(f"Time taken: {time_taken} seconds")

time_taken = timeit.timeit(lambda: list(ist), number=10000)
print(f"Time taken: {time_taken} seconds")

exit()

for a in zip([1, 2], [3, 4]):
    print(a)


async def asyncfunc():
    print("Hello World")


def func():
    asyncio.create_task(asyncfunc())


async def main():
    func()
    while True:
        await asyncio.sleep(1)


asyncio.run(main())
