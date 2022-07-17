import asyncio
import aioredis
from redisipc import IPC


async def main():
    pool = await aioredis.from_url("redis://localhost")
    ipc = IPC(pool)
    task = asyncio.create_task(ipc.start())
    try:
        response = await ipc.get('hello')
    except asyncio.TimeoutError:
        print("We timed out")
    else:
        print("Data provided by the first producer of handle_hello:", response)
    resp = await ipc.get("data", my_data="Hi Coders!")
    print(f"Response from handle_data: {resp}")
    await ipc.close()
    task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
