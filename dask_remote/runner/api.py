import math
from multiprocessing import Process
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import RedirectResponse

from .cluster_process import ClusterProcessProxy


class MessageResponse(BaseModel):
    message: str


def cluster_api(
    cluster_proxy: Optional[ClusterProcessProxy] = None, fastapi_kwargs: Optional[dict] = None
) -> FastAPI:
    """Create a FastAPI app that exposes given ClusterProcessProxy."""
    fastapi_kwargs = fastapi_kwargs or {}
    app = FastAPI(**fastapi_kwargs)
    app.cluster = cluster_proxy

    @app.get("/", summary="Redirect to swagger docs")
    async def root():
        """Redirect to API docs."""
        response = RedirectResponse(url=f"{app.openapi_prefix}/docs")
        return response

    @app.get("/status", response_model=MessageResponse)
    async def status():
        return MessageResponse(message=app.cluster.status)

    @app.get("/scheduler_address", response_model=MessageResponse)
    async def scheduler_address():
        return MessageResponse(message=app.cluster.scheduler_address)

    @app.get("/scale", response_model=MessageResponse)
    async def scale():
        """Get current number of workers."""
        return MessageResponse(message=str(app.cluster.num_workers))

    @app.post("/scale/{n}", response_model=MessageResponse)
    async def scale(n: int):
        """Scale to `n` workers."""
        if n < 0:
            n = 0
        app.cluster._adaptive_stop()
        response = app.cluster.scale(n)
        return MessageResponse(message=str(response))

    @app.post("/adapt", response_model=MessageResponse)
    async def adapt(minimum: int = 0, maximum: Optional[int] = None):
        """Set cluster to adaptive scaling mode."""
        if maximum is None:
            maximum = math.inf
        response = app.cluster.adapt(minimum=minimum, maximum=maximum)
        return MessageResponse(message=str(response))

    return app


class ApiProcess(Process):
    def __init__(
        self,
        cluster_proxy: ClusterProcessProxy,
        fastapi_kwargs: Optional[dict] = None,
        uvicorn_kwargs: Optional[dict] = None,
    ):
        self.cluster_proxy = cluster_proxy
        self.fastapi_kwargs = fastapi_kwargs or {}
        self.uvicorn_kwargs = uvicorn_kwargs or {}
        super().__init__()

    @property
    def app(self) -> FastAPI:
        return cluster_api(self.cluster_proxy, fastapi_kwargs=self.fastapi_kwargs)

    def run(self):
        import uvicorn

        uvicorn.run(self.app, **self.uvicorn_kwargs)
