import asyncio
import aioredis
from ipc import IPC

async def main():
    pool = await aioredis.from_url("redis://localhost")
    client = IPC(pool)
    t = asyncio.create_task(client.start())
    try:
        r = await client.get('hello')
    except asyncio.TimeoutError:
        pass
    else:
        print(r)
    finally:
        await client.close()
        t.cancel()

if __name__ == "__main__":
    asyncio.run(main())
