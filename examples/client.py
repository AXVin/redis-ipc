import asyncio
import aioredis
from redisipc import IPC


async def main():
    pool = await aioredis.from_url("redis://localhost")
    ipc = IPC(pool)
    task = asyncio.create_task(ipc.start())
    await asyncio.sleep(3)
    # Get the first response from any producer, also handle timeouts
    try:
        response = await ipc.get('hello')
    except asyncio.TimeoutError:
        print("We timed out")
    else:
        print("Data provided by the first producer of handle_hello:", response)
    # we won't be handling timeouts in further examples
    # but you should definitely do so as it is best practice

    # Providing some data to the producer with our request
    resp = await ipc.get("data", my_data="Hi Coders!")
    print(f"Response from handle_data: {resp}")

    # This request will only receive data from a Server with identity set to "star"
    resp2 = await ipc.get("data", required_identity="star", my_data="Can only be seen by star")
    print(f"Response from star: {resp2}")

    await ipc.close()
    task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
