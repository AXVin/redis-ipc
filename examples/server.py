import asyncio
import logging
from typing import Dict
import aioredis
from redisipc import IPC

logging.basicConfig(level=logging.INFO)


class Server(IPC):
    async def handle_hello(self):
        return {"hello": "world"}  # this will be sent to the requestor

    async def handle_data(self, data: Dict):
        data["ack"] = "The message was successfully received by the server!"
        return data  # can return the same data object after mutating

    async def on_error(self, error: Exception, message):
        print(f"Got error: {error}\n\nMessage: {message}")

    async def handle_will_error(self):
        raise RuntimeError("We errored!")


async def main():
    pool = await aioredis.from_url('redis://localhost')
    ipc = Server(pool, identity="star")  # providing an identity is optional
    try:
        await ipc.start()
    finally:
        await ipc.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
