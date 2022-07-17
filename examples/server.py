import asyncio
from typing import Dict
import aioredis
from redisipc import IPC


class Server(IPC):
    async def handle_hello(self):
        return {"hello": "world"}

    async def handle_data(self, data: Dict):
        data["ack"] = "The message was successfully received by the server!"
        return data


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
