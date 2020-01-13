import asyncio

from distributed.core import rpc
from distributed.deploy.cluster import Cluster
from distributed.security import Security
from distributed.utils import LoopRunner

from .adaptive import StatelessAdaptive
from .k8s import get_AppsV1Api, k8s_config


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


class DeploymentCluster(AsyncContextCluster):
    def __init__(
        self,
        remote_scheduler,
        deployment_name=None,
        namespace=None,
        in_cluster=False,
        config_file=None,
        asynchronous=False,
        loop=None,
        security=None,
    ):
        self.remote_scheduler = remote_scheduler
        self.deployment_name = deployment_name
        self.namespace = namespace
        self.in_cluster = in_cluster
        self.config_file = config_file
        self.app_api = None
        self.security = security
        self._scheduler_comm = None
        self._scaling_target = None
        self._scaling_task_waiting = None
        super().__init__(asynchronous=asynchronous, loop=loop)

    def _new_scheduler_comm(self):
        security = self.security or Security()
        return rpc(self.remote_scheduler, connection_args=security.get_connection_args("client"))

    @property
    def scheduler_comm(self):
        if not self._scheduler_comm:
            self._scheduler_comm = self._new_scheduler_comm()
        return self._scheduler_comm

    @property
    def workers(self):
        """Believe your eyes only."""
        return self.observed

    async def _start(self):
        await super()._start()
        self._lock = asyncio.Lock()
        await k8s_config(in_cluster=self.in_cluster, config_file=self.config_file)
        self.app_api = get_AppsV1Api()

    async def _close(self):
        await self._scale_to_target()
        await super()._close()

    async def _scale_to_target(self):
        async with self._lock:
            self._scaling_task_waiting = None
            if self._scaling_target is None:
                return
            body = {"spec": {"replicas": self._scaling_target}}
            await self.app_api.patch_namespaced_deployment_scale_with_http_info(
                name=self.deployment_name, namespace=self.namespace, body=body
            )
            self._scaling_target = None

    def _scale(self):
        if not self._scaling_task_waiting:
            self._scaling_task_waiting = asyncio.ensure_future(self._scale_to_target())
        return self._scaling_task_waiting

    def scale(self, n):
        self._scaling_target = n
        self.loop.add_callback(self._scale)
        if self.asynchronous:
            return NoOpAwaitable()

    def adapt(self, **kwargs):
        """Use a Deployment-adjuster Adaptive.

        The workers are not closed, leaving it up to the Deployment.
        """
        return super().adapt(Adaptive=StatelessAdaptive, **kwargs)