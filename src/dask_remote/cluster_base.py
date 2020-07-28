import asyncio

from distributed.core import rpc
from distributed.deploy.cluster import Cluster
from distributed.security import Security
from distributed.utils import LoopRunner


class NoOpAwaitable(object):
    """An awaitable object that always returns None.

    Useful to return from a method that can be called in both asynchronous and
    synchronous contexts.

    From `distributed.deploy.spec`.
    """

    def __await__(self):
        async def f():
            return None

        return f().__await__()


class ContextCluster(Cluster):
    def __init__(self, asynchronous=False, loop=None):
        self._loop_runner = LoopRunner(loop=loop, asynchronous=asynchronous)
        self.loop = self._loop_runner.loop

        super().__init__(asynchronous=asynchronous)

        if not self.asynchronous:
            self._loop_runner.start()
            self.sync(self._start)

    def __enter__(self):
        if self.status != "running":
            raise ValueError(f"Expected status 'running', found '{self.status}'")
        return self

    def __exit__(self, typ, value, traceback):
        self.close()
        self._loop_runner.stop()


class AsyncContextCluster(ContextCluster):
    def __await__(self):
        async def _():
            if self.status == "created":
                await self._start()
            return self

        return _().__await__()

    async def __aenter__(self):
        await self
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.close()


class RemoteSchedulerCluster(AsyncContextCluster):
    def __init__(self, asynchronous=False, loop=None, security=None):
        self.security = security or Security()
        super().__init__(asynchronous=asynchronous, loop=loop)

    async def _start(self):
        self.status: str
        while self.status == "starting":
            await asyncio.sleep(0.01)
        if self.status == "running":
            return
        if self.status == "closed":
            raise ValueError("Unexpected 'closed' status")

        self.status = "starting"
        self.scheduler_comm = rpc(
            self.scheduler_address, connection_args=self.security.get_connection_args("client")
        )
        await super()._start()
