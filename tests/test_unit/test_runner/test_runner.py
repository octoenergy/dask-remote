from multiprocessing import Pipe

import pytest

from dask_remote.runner.runner import ClusterProcess, ClusterProcessProxy


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


class TestClusterProcess:
    @pytest.mark.parametrize("n", [0, 42])
    def test_cluster_kwargs(self, n, cmd_pipe, result_pipe):
        cluster_process = ClusterProcess(
            cmd_conn=cmd_pipe[1],
            result_conn=result_pipe[0],
            cluster_cls=PingCluster,
            cluster_kwargs={"n": n},
        )
        cluster_process.start()

        cmd = {"attribute": "scheduler_info"}
        cmd_pipe[0].send(cmd)
        info = result_pipe[1].recv()

        assert len(info["workers"]) == n

        cluster_process.terminate()
        cluster_process.join()

    def test_attribute(self, cluster_process, cmd_pipe, result_pipe):
        cmd = {"attribute": "attribute"}
        cmd_pipe[0].send(cmd)
        result = result_pipe[1].recv()

        assert result == "attribute"

    @pytest.mark.parametrize(
        "cmd", [{"method": "method", "args": [42]}, {"method": "method", "kwargs": {"n": 42}}]
    )
    def test_method(self, cluster_process, cmd_pipe, result_pipe, cmd):
        cmd_pipe[0].send(cmd)
        result = result_pipe[1].recv()

        assert result == "method(42)"

    def test_returns_error(self, cluster_process, cmd_pipe, result_pipe):
        cmd = {"attribute": "not_an_attribute"}
        cmd_pipe[0].send(cmd)
        result = result_pipe[1].recv()

        assert isinstance(result, AttributeError)


@pytest.fixture
def cluster_process_proxy(cmd_pipe, result_pipe):
    cluster_process_proxy = ClusterProcessProxy(cmd_conn=cmd_pipe[0], result_conn=result_pipe[1])
    return cluster_process_proxy


class TestClusterProcessProxy:
    @pytest.mark.parametrize("attr", ["scheduler_address"])
    def test_cluster_attribute(self, cluster_process_proxy, cmd_pipe, result_pipe, attr):
        result_pipe[0].send(None)  # fake a response
        _ = cluster_process_proxy.scheduler_address
        cmd = cmd_pipe[1].recv()

        assert cmd == {"attribute": attr}

    @pytest.mark.parametrize(
        "method, args, kwargs", [("scale", (42,), {}), ("scale", (), {"n": 42})]
    )
    def test_cluster_method(
        self, cluster_process_proxy, cmd_pipe, result_pipe, method, args, kwargs
    ):
        result_pipe[0].send(None)  # fake a response
        _ = cluster_process_proxy.scale(*args, **kwargs)
        cmd = cmd_pipe[1].recv()

        assert cmd == {"method": method, "args": args, "kwargs": kwargs}

    def test_not_cluster_attribute(self, cluster_process_proxy):
        with pytest.raises(AttributeError):
            _ = cluster_process_proxy.not_an_attribute

    def test_not_cluster_method(self, cluster_process_proxy):
        with pytest.raises(AttributeError):
            _ = cluster_process_proxy.not_a_method()


class TestIntegration:
    def test_attribute(self, cluster_process, cluster_process_proxy):
        assert cluster_process_proxy.scheduler_address == "scheduler_address"

    def test_method(self, cluster_process, cluster_process_proxy):
        assert cluster_process_proxy.scale(42) == f"scale(42)"

    def test_new_attribute(self, cluster_process, cluster_process_proxy):
        """Test attribute that is valid, but not part of the original cluster class."""
        assert cluster_process_proxy.num_workers == 0
