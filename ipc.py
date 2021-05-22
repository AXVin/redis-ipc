import os
import json
from typing import Dict
import secrets
import asyncio

import aioredis


def random_hex(bytes=16):
    return os.urandom(bytes).hex()

class IPC:
    def __init__(self, loop=None, pool=None,
                 channel="ipc:1", identity=None):
        self.redis = pool
        self.channel_address = channel
        self.identity = identity or random_hex()
        self.loop = loop or asyncio.get_event_loop()
        self.channel = None
        self.handlers = {
            method.lstrip("handle_"): getattr(self, method)
            for method in dir(self)
            if method.startswith("handle_")
        }
        self.nonces: Dict[str, asyncio.Future] = {}
        self.task = self.loop.create_task(self.listen_ipc())


    def add_handler(self, name, func):
        self.handlers[name] = func


    def remove_handler(self, name):
        del self.handlers[name]


    async def publish(self, op: str, **data):
        """
        A normal publish to the current channel
        with no expectations of any returns
        """
        data["op"] = op
        data = json.dumps(data)
        await self.redis.publish(self.channel_address, data)


    async def get(self, op, *, timeout=5, **data):
        """
        An IPC call to get a response back

        Parameters:
        -----------
        op: str
            The operation to call on the other process
        timeout: int
            How long to wait for a response
        data: kwargs
            The data to be sent

        Returns:
        --------
        dict:
            The data sent by the first response
        """
        nonce = random_hex()
        # data["op"] = op
        data["nonce"] = nonce
        data["sender"] = self.identity

        future = self.loop.create_future()
        self.nonces[nonce] = future

        try:
            await self.publish(op, **data)
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            del self.nonces[nonce]


    async def _run_handler(self, handler, message, nonce):
        try:
            resp = await handler(message)
            if resp and nonce:
                resp["nonce"] = nonce
                resp["sender"] = self.identity
                resp = json.dumps(resp)
                await self.redis.publish(self.channel_address, resp)
        except asyncio.CancelledError:
            pass

    async def ensure_channel(self):
        if self.channel is None:
            pubsub = self.channel = self.redis.pubsub()
            await pubsub.subscribe(self.channel_address)


    async def listen_ipc(self):
        try:
            await self.ensure_channel()
            print(self.channel, dir(self.channel))
            async for message in self.channel.listen():
                message = json.loads(message)
                op = message.pop("op")
                nonce = message.pop("nonce", None)
                sender = message.pop("sender", None)
                if sender != self.identity and nonce in self.nonces:
                    future = self.nonces[nonce]
                    future.set_result(message)
                    continue
     
                handler = self.handlers.get(op)
                if handler:
                    wrapped = self._run_handler(handler, message, nonce)
                    asyncio.create_task(wrapped,
                                        name=f"redis-ipc: {op}")
        except asyncio.CancelledError:
            await self.channel.unsubscribe(self.channel_address)


    async def start(self):
        """
        Starts the IPC server
        """
        await self.listen_ipc()


    async def close(self):
        """
        Close the IPC reciever
        """
        self.task.cancel()
        await self.channel.unsubscribe(self.channel_address)
