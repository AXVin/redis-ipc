# Redis IPC
The redis ipc server and client

Creates a redis ipc server that listens on a single pub/sub channel
and allows you to communicate between multiple processes

Subclass the IPC class and add your handlers as methods
like this
```python
async def handle_channel_update(self, data):
    return data
```
or use `IPC.add_handler` to add the handler after the
class has been instantiated


and whenever a process calls `IPC.get`, all the clients connected to
that channel will try to handle the request and whichever one finishes
first, will be return by the function

the handler must either return a dict or `None`
`None` is treated has an implicit reason that the current
process doesn't matches the requests' target process
