import asyncio
import aioredis
from ipc import IPC

class Server(IPC):

    async def handle_hello(self):
        return {"hello": "world"}


async def main():
    pool = await aioredis.from_url('redis://localhost')
    s = Server(pool)
    try:
        await s.start()
    finally:
        await s.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
