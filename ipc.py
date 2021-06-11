import os
import json
from typing import Any, Coroutine, Dict, Callable, List, Optional, TypedDict, Union
import asyncio

JSON = Optional[Union[str, float, bool, List['JSON'], Dict[str, 'JSON']]]
Handler = Callable[[Optional[JSON]], Coroutine[Any, Any, JSON]] 


class _BaseIPCMessage(TypedDict, total=False):
    op: str
    data: JSON
    nonce: str

class IPCMessage(_BaseIPCMessage):
    sender: str


def random_hex(bytes: int = 16) -> str:
    return os.urandom(bytes).hex()

class IPC:
    def __init__(self, pool, loop=None,
            channel: str = "ipc:1", identity: str = None) -> None:
        self.redis = pool
        self.channel_address = channel
        self.identity = identity or random_hex()
        self.loop = loop or asyncio.get_event_loop()
        self.channel = None
        self.handlers: Dict[str, Handler] = {
            method.replace("handle_", ""): getattr(self, method)
            for method in dir(self)
            if method.startswith("handle_")
        }
        self.nonces: Dict[str, asyncio.Future] = {}


    def add_handler(self, name: str, func: Handler) -> None:
        self.handlers[name] = func


    def remove_handler(self, name: str) -> None:
        del self.handlers[name]


    async def publish(self, op: str, **data) -> None:
        """
        A normal publish to the current channel
        with no expectations of any returns
        """
        data["op"] = op
        data = json.dumps(data)
        await self.redis.publish(self.channel_address, data)


    async def get(self, op: str, *, timeout: int = 5, **data: JSON):
        """
        An IPC call to get a response back

        Parameters:
        -----------
        op: str
            The operation to call on the other processes
        timeout: int
            How long to wait for a response
        data: kwargs
            The data to be sent

        Returns:
        --------
        dict:
            The data sent by the first response

        Raises:
        -------
        asyncio.errors.TimeoutError:
            when timeout runs out
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


    async def handle_hello(self, message: JSON) -> JSON:
        return {'hello': 'world'}



    async def _run_handler(self, handler: Handler,
                           nonce: str, message: JSON = None) -> None:
        try:
            resp = await handler(message)

            if resp and nonce:
                data: IPCMessage = {
                    'nonce': nonce,
                    'sender': self.identity,
                    'data': resp
                }
                resp = json.dumps(data)
                await self.redis.publish(self.channel_address, resp)
        except asyncio.CancelledError:
            pass

    async def ensure_channel(self) -> None:
        if self.channel is None:
            pubsub = self.channel = self.redis.pubsub()
            await pubsub.subscribe(self.channel_address)


    async def listen_ipc(self) -> None:
        try:
            await self.ensure_channel()
            async for message in self.channel.listen():
                if message.get("type") != "message":
                    continue
                data: Union[str, bytes] = message['data']
                message: IPCMessage = json.loads(data)
                op = message.pop("op", None)
                nonce = message.pop("nonce", None)
                sender = message.pop("sender", None)
                if op is None and sender != self.identity and nonce in self.nonces:
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
        await self.channel.unsubscribe(self.channel_address)
