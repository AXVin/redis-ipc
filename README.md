# Redis IPC
A lightweight multiple producer and single consumer IPC server
that uses redis pubsub as a broker

Creates a redis ipc server that listens on a single pub/sub channel
and allows you to communicate between multiple processes

Subclass the IPC class and add your handlers as methods
like this (handlers must start with `handle_` as their name)
```python
async def handle_channel_update(self, data):
    return data
```
or use `IPC.add_handler` to add the handler after the
class has been instantiated


and whenever a process calls `IPC.get`, all the clients connected to
that channel will try to handle the request and whichever one finishes
first, will be returned by the function

the handler must either return a dict or `None`
`None` is treated as an implicit reason that the current
process doesn't matches the requests' target process
