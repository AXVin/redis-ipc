import asyncio
import aioredis
from ipc import IPC

async def main():
  pool = await aioredis.from_url("redis://localhost")
  client = IPC(pool=pool)
  t = asyncio.create_task(client.start())
  r = await client.get('hello')
  print(r)
  t.cancel()

if __name__ == "__main__":
  asyncio.run(main())
