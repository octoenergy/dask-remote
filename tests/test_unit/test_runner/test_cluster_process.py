import pytest

from dask_remote.runner.cluster_process import ClusterProcess

from .conftest import PingCluster


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


class TestClusterProcess:
    @pytest.mark.parametrize("n", [0, 42])
    def test_cluster_kwargs(self, n):
        cluster_process = ClusterProcess(cluster_cls=PingCluster, cluster_kwargs={"n": n})
        cluster_process.start()

        cmd = {"attribute": "scheduler_info"}
        cluster_process._cmd_pipe[0].send(cmd)
        info = cluster_process._result_pipe[1].recv()

        assert len(info["workers"]) == n

        cluster_process.terminate()
        cluster_process.join()

    def test_attribute(self, cluster_process):
        cmd = {"attribute": "attribute"}
        cluster_process._cmd_pipe[0].send(cmd)
        result = cluster_process._result_pipe[1].recv()

        assert result == "attribute"

    @pytest.mark.parametrize(
        "cmd", [{"method": "method", "args": [42]}, {"method": "method", "kwargs": {"n": 42}}]
    )
    def test_method(self, cluster_process, cmd):
        cluster_process._cmd_pipe[0].send(cmd)
        result = cluster_process._result_pipe[1].recv()

        assert result == "method(42)"

    def test_returns_error(self, cluster_process):
        cmd = {"attribute": "not_an_attribute"}
        cluster_process._cmd_pipe[0].send(cmd)
        result = cluster_process._result_pipe[1].recv()

        assert isinstance(result, AttributeError)

    def test_proxy(self, cluster_process):
        proxy = cluster_process.proxy
        assert proxy.cmd_conn is cluster_process._cmd_pipe[0]
        assert proxy.result_conn is cluster_process._result_pipe[1]


class TestIntegration:
    def test_attribute(self, cluster_process):
        assert cluster_process.proxy.scheduler_address == "scheduler_address"

    def test_method(self, cluster_process, cluster_process_proxy):
        assert cluster_process.proxy.scale(42) == f"scale(42)"

    def test_new_attribute(self, cluster_process, cluster_process_proxy):
        """Test attribute that is valid, but not part of the original cluster class."""
        assert cluster_process.proxy.num_workers == 0
