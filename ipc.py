import json
import secrets
import asyncio

import aioredis

NONCE_BYTES = 8


class IPC:
    def __init__(self, loop=None, pool=None,
                 channel="ipc:1", identity=None):
        self.redis = pool
        self.channel_address = channel
        self.identity = identity or secrets.token_hex(NONCE_BYTES)
        self.loop = loop or asyncio.get_event_loop()
        self.channel = None
        self.handlers = {
            method.lstrip("handle_"): getattr(self, method)
            for method in dir(self)
            if method.startswith("handle_")
        }
        self.nonces = {} # nonce: Future
        self.task = self.loop.create_task(self.listen_ipc)


    def add_handler(self, name, func):
        self.handlers[name] = func


    def remove_handler(self, name):
        del self.handlers[name]


    async def ensure_channel(self):
        if self.channel is None:
            self.channel = await self.redis.subscribe(self.channel_address)


    async def publish(self, op, **data):
        """
        A normal publish to the current channel
        with no expectations of any returns
        """
        data["op"] = op
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
        await self.ensure_channel()
        nonce = secrets.token_hex(NONCE_BYTES)
        data["op"] = op
        data["nonce"] = nonce
        data["sender"] = self.identity

        future = self.loop.create_future()
        self.nonces[nonce] = future

        try:
            await self.redis.publish(self.channel_address, data)
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            del self.nonces[nonce]


    async def _run_handler(self, handler, message, nonce):
        try:
            resp = await handler(self, message)
            if resp and nonce:
                resp["nonce"] = nonce
                resp["sender"] = self.identity
                await self.redis.publish(self.channel_address, resp)
        except asyncio.CancelledError:
            pass


    async def listen_ipc(self):
        await self.ensure_channel()

        async for message in self.channel.iter(encoding="utf-8", decoder=json.loads):
            op = message.pop("op")
            nonce = message.pop("nonce", None)
            sender = message.pop("sender", None)
            if sender != self.identity and nonce in self.nonces:
                future = self.nonces[nonce]
                future.set_result(message)
                continue
 
            handler = self.handler.get(op)
            if handler:
                wrapped = self._run_handler(handler, message, nonce)
                asyncio.create_task(wrapped,
                                    name=f"redis-ipc: {op}")



    async def close(self):
        """
        Close the IPC reciever
        """
        self.task.cancel()
        await self.redis.unsubscribe(self.channel_address)
