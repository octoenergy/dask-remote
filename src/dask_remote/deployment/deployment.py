import asyncio

from ..cluster_base import NoOpAwaitable, RemoteSchedulerCluster
from .adaptive import StatelessAdaptive
from .k8s import get_AppsV1Api, k8s_config


class DeploymentCluster(RemoteSchedulerCluster):
    def __init__(
        self,
        scheduler_address,
        deployment_name=None,
        namespace=None,
        in_cluster=False,
        config_file=None,
        asynchronous=False,
        loop=None,
        security=None,
    ):
        self.scheduler_address = scheduler_address
        self.deployment_name = deployment_name
        self.namespace = namespace
        self.in_cluster = in_cluster
        self.config_file = config_file
        self.app_api = None
        self._scaling_target = None
        self._scaling_task_waiting = None
        super().__init__(asynchronous=asynchronous, loop=loop, security=security)

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
            await self.app_api.patch_namespaced_deployment_scale_with_http_info(  # type: ignore
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
