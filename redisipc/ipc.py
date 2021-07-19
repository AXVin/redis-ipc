"""
Copyright (C) 2021-present  AXVin

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


import os
import json
from typing import Any, Coroutine, Dict, Callable, List, Optional, TypedDict, Union
import asyncio

from asyncio.events import AbstractEventLoop
from aioredis import Redis

__all__ = (
    'JSON',
    'IPC',
    'Handler',
)


JSON = Optional[Union[str, float, bool, List['JSON'], Dict[str, 'JSON']]]
Handler = Callable[[Optional[JSON]], Coroutine[Any, Any, JSON]]


class _BaseIPCMessage(TypedDict, total=False):
    op: str
    data: JSON
    nonce: str


class IPCMessage(_BaseIPCMessage):
    sender: str


def random_hex(_bytes: int = 16) -> str:
    return os.urandom(_bytes).hex()


class IPC:
    def __init__(
        self,
        pool: Redis,
        loop: AbstractEventLoop = None,
        channel: str = "ipc:1",
        identity: str = None,
    ) -> None:
        self.redis = pool
        self.channel_address = channel
        self.identity = identity or random_hex()
        self.loop = loop or asyncio.get_running_loop()
        self.channel = None
        self.handlers: Dict[str, Handler] = {
            method.replace("handle_", ""): getattr(self, method)
            for method in dir(self)
            if method.startswith("handle_")
        }
        self.nonces: Dict[str, asyncio.Future[JSON]] = {}

    def add_handler(self, name: str, func: Handler) -> None:
        self.handlers[name] = func

    def remove_handler(self, name: str) -> None:
        del self.handlers[name]

    async def publish(self, op: str, **data: JSON) -> None:
        """
        A normal publish to the current channel
        with no expectations of any returns
        """
        data["op"] = op
        resp = json.dumps(data)
        await self.redis.publish(self.channel_address, resp)

    async def get(self, op: str, *, timeout: int = 5, **data: JSON) -> JSON:
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

        future: asyncio.Future[JSON] = self.loop.create_future()
        self.nonces[nonce] = future

        try:
            await self.publish(op, **data)
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            del self.nonces[nonce]

    async def _run_handler(self, handler: Handler, nonce: Optional[str], message: JSON = None) -> None:
        try:
            if message:
                resp = await handler(message)
            else:
                resp = await handler()  # type: ignore

            if resp and nonce:
                data: IPCMessage = {
                    'nonce': nonce,
                    'sender': self.identity,
                    'data': resp,
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
            async for msg in self.channel.listen():
                if msg.get("type") != "message":
                    continue
                message: IPCMessage = json.loads(msg.get('data'))
                op = message.get("op")
                nonce = message.get("nonce")
                sender = message.get("sender")
                data = message.get('data')
                if op is None and sender != self.identity and nonce is not None and nonce in self.nonces:
                    future = self.nonces.get(nonce)
                    future.set_result(data)
                    continue

                handler = self.handlers.get(op)  # type: ignore
                if handler:
                    wrapped = self._run_handler(handler, message=data, nonce=nonce)
                    asyncio.create_task(wrapped, name=f"redis-ipc: {op}")
        except asyncio.CancelledError:
            await self.channel.unsubscribe(self.channel_address)

    async def start(self) -> None:
        """
        Starts the IPC server
        """
        await self.listen_ipc()

    async def close(self) -> None:
        """
        Close the IPC reciever
        """
        await self.channel.unsubscribe(self.channel_address)
