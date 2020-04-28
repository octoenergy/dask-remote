import math
from multiprocessing import Process
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel, constr
from starlette.responses import RedirectResponse

from .cluster_process import ClusterProcessProxy


class ResponseMessage(BaseModel):
    message: str


class WorkerInfo(BaseModel):
    type: constr(regex="^Worker$")
    id: Any
    host: Optional[str]
    nanny: Optional[str]
    name: Optional[Any]
    nthreads: int
    memory_limit: int
    services: Dict[str, Any]
    resources: Dict[str, Any]
    local_directory: Optional[str]


class SchedulerInfo(BaseModel):
    type: constr(regex="^Scheduler$")
    id: Any
    address: Optional[str]
    services: Dict[str, Any]
    workers: Dict[Any, WorkerInfo]


def cluster_api(
    cluster_proxy: Optional[ClusterProcessProxy] = None,
    fastapi_kwargs: Optional[dict] = None,
    scheduler_address: Optional[str] = None,
    dashboard_link: Optional[str] = None,
) -> FastAPI:
    """Create a FastAPI app that exposes given ClusterProcessProxy.

    Params:
        cluster_proxy: a `ClusterProcessProxy` for the cluster process (sic)
        fastapi_kwargs: additional keyword arguments passed to `fastapi.FastAPI`
        scheduler_address: override value for the RPC address used by remote clients
        dashboard_link: override value for the HTTP link to the dashboard displayed to clients

    Configuring `scheduler_address` and `dashboard_link` is necessary when the API runs
    behind a reverse proxy, or when we want to support DNS/domain names.
    """
    fastapi_kwargs = fastapi_kwargs or {}
    app = FastAPI(**fastapi_kwargs)
    app.dask_cluster_proxy = cluster_proxy
    app.dask_scheduler_address = scheduler_address
    app.dask_dashboard_link = dashboard_link

    @app.get("/", summary="Redirect to this page")
    async def root():
        """Redirect to API docs."""
        response = RedirectResponse(url=f"{app.openapi_prefix}/docs")
        return response

    @app.get("/status", summary="Cluster status", response_model=ResponseMessage)
    async def status():
        """Return cluster status, e.g. 'running'."""
        return ResponseMessage(message=app.dask_cluster_proxy.status)

    @app.get("/scheduler_address", summary="Scheduler address", response_model=ResponseMessage)
    async def scheduler_address():
        """Return public scheduler address for use by RPC clients."""
        scheduler_address = app.dask_scheduler_address or app.dask_cluster_proxy.scheduler_address
        return ResponseMessage(message=scheduler_address)

    @app.get("/scheduler_info", response_model=SchedulerInfo)
    async def scheduler_info():
        return SchedulerInfo(**app.dask_cluster_proxy.scheduler_info)

    @app.get(
        "/dashboard_link", summary="Link to monitoring dashboard", response_model=ResponseMessage
    )
    async def scheduler_address():
        """Return public link to monitoring dashboard."""
        dashboard_link = app.dask_dashboard_link or app.dask_cluster_proxy.dashboard_link
        return ResponseMessage(message=dashboard_link)

    @app.get("/scale", summary="Current number of workers", response_model=ResponseMessage)
    async def scale():
        """Return current number of workers."""
        return ResponseMessage(message=str(app.dask_cluster_proxy.num_workers))

    @app.post("/scale", summary="Scale to desired size", response_model=ResponseMessage)
    async def scale(n: int):
        """Scale to `n` workers."""
        if n < 0:
            n = 0
        app.dask_cluster_proxy._adaptive_stop()
        response = app.dask_cluster_proxy.scale(n)
        return ResponseMessage(message=str(response))

    @app.post("/adapt", summary="Set adaptive scaling", response_model=ResponseMessage)
    async def adapt(minimum: int = 0, maximum: Optional[int] = None):
        """Set cluster to adaptive scaling mode."""
        if maximum is None:
            maximum = math.inf
        response = app.dask_cluster_proxy.adapt(minimum=minimum, maximum=maximum)
        return ResponseMessage(message=str(response))

    return app


class ApiProcess(Process):
    def __init__(
        self,
        cluster_proxy: ClusterProcessProxy,
        fastapi_kwargs: Optional[dict] = None,
        uvicorn_kwargs: Optional[dict] = None,
        scheduler_address: Optional[str] = None,
        dashboard_link: Optional[str] = None,
    ):
        self.cluster_proxy = cluster_proxy
        self.fastapi_kwargs = fastapi_kwargs
        self.uvicorn_kwargs = uvicorn_kwargs
        self.scheduler_address = scheduler_address
        self.dashboard_link = dashboard_link
        super().__init__()

    @property
    def app(self) -> FastAPI:
        return cluster_api(
            self.cluster_proxy,
            fastapi_kwargs=self.fastapi_kwargs,
            scheduler_address=self.scheduler_address,
            dashboard_link=self.dashboard_link,
        )

    def run(self):
        import uvicorn

        kwargs = self.uvicorn_kwargs or {}
        uvicorn.run(self.app, **kwargs)
