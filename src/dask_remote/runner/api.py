from multiprocessing import Process
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import RedirectResponse
from typing_extensions import Literal

from .cluster_process import ClusterProcessProxy


class ResponseMessage(BaseModel):
    message: str


class WorkerInfo(BaseModel):
    type: Literal["Worker"]
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
    type: Literal["Scheduler"]
    id: Any
    address: Optional[str]
    services: Dict[str, Any]
    workers: Dict[Any, WorkerInfo]


class DaskAPI(FastAPI):
    dask_cluster_proxy: ClusterProcessProxy
    dask_scheduler_address: Optional[str] = None
    dask_dashboard_link: Optional[str] = None


def cluster_api(
    cluster_proxy: ClusterProcessProxy,
    fastapi_kwargs: Optional[dict] = None,
    scheduler_address: Optional[str] = None,
    dashboard_link: Optional[str] = None,
) -> DaskAPI:
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
    app = DaskAPI(**fastapi_kwargs)
    app.dask_cluster_proxy = cluster_proxy
    app.dask_scheduler_address = scheduler_address
    app.dask_dashboard_link = dashboard_link

    @app.get("/", include_in_schema=False)
    async def redirect_root():
        """Redirect to API docs."""
        return RedirectResponse(url=f"{app.root_path}/docs")

    @app.get("/status", summary="Cluster status", response_model=ResponseMessage)
    async def get_status():
        """Return cluster status, e.g. 'running'."""
        return ResponseMessage(message=app.dask_cluster_proxy.status)

    @app.get("/scheduler_address", summary="Scheduler address", response_model=ResponseMessage)
    async def get_scheduler_address():
        """Return public scheduler address for use by RPC clients."""
        scheduler_address = app.dask_scheduler_address or app.dask_cluster_proxy.scheduler_address
        return ResponseMessage(message=scheduler_address)

    @app.get("/scheduler_info", response_model=SchedulerInfo)
    async def get_scheduler_info():
        return SchedulerInfo(**app.dask_cluster_proxy.scheduler_info)

    @app.get(
        "/dashboard_link", summary="Link to monitoring dashboard", response_model=ResponseMessage
    )
    async def get_dashboard_link():
        """Return public link to monitoring dashboard."""
        dashboard_link = app.dask_dashboard_link or app.dask_cluster_proxy.dashboard_link
        return ResponseMessage(message=dashboard_link)

    @app.get("/scale", summary="Current number of workers", response_model=ResponseMessage)
    async def get_scale():
        """Return current number of workers."""
        return ResponseMessage(message=str(app.dask_cluster_proxy.num_workers))

    @app.post("/scale", summary="Scale to desired size", response_model=ResponseMessage)
    async def set_scale(n: int):
        """Scale to `n` workers."""
        if n < 0:
            n = 0
        app.dask_cluster_proxy._adaptive_stop()
        response = app.dask_cluster_proxy.scale(n)
        return ResponseMessage(message=str(response))

    @app.post("/adapt", summary="Set adaptive scaling", response_model=ResponseMessage)
    async def set_adapt(minimum: int = 0, maximum: Optional[int] = None):
        """Set cluster to adaptive scaling mode."""
        response = app.dask_cluster_proxy.adapt(minimum=minimum, maximum=maximum or 999999)
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
    ) -> None:
        self.cluster_proxy = cluster_proxy
        self.fastapi_kwargs = fastapi_kwargs
        self.uvicorn_kwargs = uvicorn_kwargs
        self.scheduler_address = scheduler_address
        self.dashboard_link = dashboard_link
        super().__init__()

    @property
    def app(self) -> DaskAPI:
        return cluster_api(
            self.cluster_proxy,
            fastapi_kwargs=self.fastapi_kwargs,
            scheduler_address=self.scheduler_address,
            dashboard_link=self.dashboard_link,
        )

    def run(self) -> None:
        import uvicorn

        kwargs = self.uvicorn_kwargs or {}
        uvicorn.run(self.app, **kwargs)
