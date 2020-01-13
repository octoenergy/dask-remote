from multiprocessing import Pipe

import pytest

from dask_remote.runner.cluster_process import ClusterProcess, ClusterProcessProxy

@pytest.fixture
def cmd_pipe():
    return Pipe()


@pytest.fixture()
def result_pipe():
    return Pipe()


class PingCluster:
    def __init__(self, n=0):
        self.scheduler_info = dict(workers=list(range(n)))
        self.workers = list(range(n))

    @property
    def scheduler_address(self):
        return "scheduler_address"

    def scale(self, n):
        return f"scale({n})"

    @property
    def attribute(self):
        return "attribute"

    def method(self, n):
        return f"method({n})"


@pytest.fixture
def cluster_process(cmd_pipe, result_pipe):
    cluster_process = ClusterProcess(
        cmd_conn=cmd_pipe[1], result_conn=result_pipe[0], cluster_cls=PingCluster
    )
    cluster_process.start()
    yield cluster_process
    cluster_process.terminate()
    cluster_process.join()


@pytest.fixture
def cluster_process_proxy(cmd_pipe, result_pipe):
    cluster_process_proxy = ClusterProcessProxy(cmd_conn=cmd_pipe[0], result_conn=result_pipe[1])
    return cluster_process_proxy
