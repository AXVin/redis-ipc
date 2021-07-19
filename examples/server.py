import asyncio
import aioredis
from redisipc import IPC


class Server(IPC):
    async def handle_hello(self):
        return {"hello": "world"}


async def main():
    pool = await aioredis.from_url('redis://localhost')
    ipc = Server(pool)
    try:
        await ipc.start()
    finally:
        await ipc.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
