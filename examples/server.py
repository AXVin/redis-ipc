import asyncio
import aioredis
from ipc import IPC

class Server(IPC):

  async def parse_hello(self):
    print(hello)
    return {"hello": "world"}


async def main():
  pool = await aioredis.from_url('redis://localhost')
  s = Server(pool=pool)
  await s.start()


if __name__ == "__main__":
  asyncio.run(main())
