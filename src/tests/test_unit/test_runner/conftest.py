from multiprocessing import Pipe

import pytest

from dask_remote.runner.api import cluster_api
from dask_remote.runner.cluster_process import ClusterProcess, ClusterProcessProxy


class PingCluster:
    def __init__(self, n=0):
        self.n = n

    @property
    def workers(self):
        return list(range(self.n))

    @property
    def status(self):
        return "running"

    @property
    def scheduler_address(self):
        return "scheduler_address"

    def scale(self, n):
        self.n = n
        return f"scale({n})"

    def adapt(self, **kwargs):
        """Not picklable."""
        return lambda: None


@pytest.fixture
def cmd_pipe():
    return Pipe()


@pytest.fixture()
def result_pipe():
    return Pipe()


@pytest.fixture
def cluster_process_proxy(cmd_pipe, result_pipe):
    cluster_process_proxy = ClusterProcessProxy(cmd_conn=cmd_pipe[0], result_conn=result_pipe[1])
    return cluster_process_proxy


@pytest.fixture
def cluster_process(cmd_pipe, result_pipe):
    cluster_process = ClusterProcess(cluster_cls=PingCluster)
    cluster_process.start()
    yield cluster_process
    cluster_process.terminate()
    cluster_process.join()


@pytest.fixture
def api_port(request):
    return request.config.getoption("--api-port")


@pytest.fixture
def api_address(api_port):
    return f"http://localhost:{api_port}"


@pytest.fixture
def api_app(cluster_process):
    return cluster_api(cluster_process.proxy)
