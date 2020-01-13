"""
Run Cluster in a separata process, and expose its scaling commands through a "proxy".

>>> from multiprocessing import Pipe
>>> from dask.distributed import LocalCluster
>>> from dask_remote import ClusterProcess, ClusterProcessProxy
>>> cmd_conn, result_conn = Pipe()
>>> cluster_proc = ClusterProcess(cmd_conn, result_conn, LocalCluster, dict(n_workers=0))
>>> cluster_proc.start()  # uses the multiprocessing.Process API
>>> cluster_proxy = ClusterProcessProxy(cmd_conn, result_conn)
>>> cluster_proxy.scale(4)  # command is proxied to the cluster object in the child process
>>> cluster_prox.join()  # cluster remains alive until terminated
"""
from multiprocessing import Process
from multiprocessing.connection import Connection
from typing import Optional, Type

from distributed.deploy.cluster import Cluster


class ClusterProcess(Process):
    """Run a dask Cluster object in a child process, and expose core methods and attributes.
    """

    def __init__(
        self,
        cmd_conn: Connection,
        result_conn: Connection,
        cluster_cls: Type[Cluster],
        cluster_kwargs: Optional[dict] = None,
    ):
        self.cluster_cls = cluster_cls
        self.cluster_kwargs = cluster_kwargs or {}
        self.cmd_conn = cmd_conn  # pipe connection to receive scaling/control commands from
        self.result_conn = result_conn  # pipe connection to return messages to
        super().__init__()

    @property
    def cluster_class(self):
        class ClusterClass(self.cluster_cls):
            @property
            def num_workers(self):
                return len(self.workers)

        return ClusterClass

    def run(self):
        cluster = self.cluster_class(**self.cluster_kwargs)
        while True:
            cmd = self.cmd_conn.recv()
            self._process_cmd(cmd, cluster)

    def _process_cmd(self, cmd, cluster):
        try:
            result = self._call_cmd(cmd, cluster)
        except Exception as e:
            result = e
        self.result_conn.send(result)

    @staticmethod
    def _call_cmd(cmd, obj):
        if "method" in cmd:
            method = cmd["method"]
            args = cmd.get("args", [])
            kwargs = cmd.get("kwargs", {})
            return getattr(obj, method)(*args, **kwargs)
        elif "attribute" in cmd:
            attribute = cmd["attribute"]
            return getattr(obj, attribute)


class ClusterProcessProxy:

    CLUSTER_ATTRIBUTES = ["dashboard_link", "scheduler_address", "scheduler_info", "num_workers"]
    CLUSTER_METHODS = ["scale", "adapt"]

    def __init__(self, cmd_conn: Connection, result_conn: Connection):
        self.cmd_conn = cmd_conn  # pipe connection to receive scaling/control commands from
        self.result_conn = result_conn  # pipe connection to return messages to

    # Client side
    def _submit_cmd(self, cmd):
        self.cmd_conn.send(cmd)
        result = self.result_conn.recv()
        if isinstance(result, Exception):
            raise result
        return result

    def _get_cluster_attribute(self, attr):
        cmd = {"attribute": attr}
        return self._submit_cmd(cmd)

    def _call_cluster_method(self, method, *args, **kwargs):
        cmd = {"method": method, "args": args, "kwargs": kwargs}
        return self._submit_cmd(cmd)

    def _get_cluster_method(self, method):
        def callable_method(*args, **kwargs):
            return self._call_cluster_method(method, *args, **kwargs)

        callable_method.__name__ = method

        return callable_method

    def __getattr__(self, attr):
        if attr in self.CLUSTER_ATTRIBUTES:
            return self._get_cluster_attribute(attr)
        elif attr in self.CLUSTER_METHODS:
            return self._get_cluster_method(attr)
        else:
            return super().__getattr__(attr)
