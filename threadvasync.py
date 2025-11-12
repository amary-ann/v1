# import threading
# import time

# def task(name):
#     time.sleep(2)
#     print(f"Task {name} done")

# for i in range(3):
#     threading.Thread(target=task, args=(i,)).start()

import asyncio

async def task(name):
    await asyncio.sleep(2)
    print(f"Task {name} done")

async def main():
    await asyncio.gather(*(task(i) for i in range(3)))

asyncio.run(main())
