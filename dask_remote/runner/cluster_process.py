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
from multiprocessing.connection import Connection, Pipe
from typing import Optional, Tuple, Type

from distributed.deploy.cluster import Cluster


class ClusterProcessProxy:

    CLUSTER_ATTRIBUTES = [
        "dashboard_link",
        "scheduler_address",
        "scheduler_info",
        "num_workers",
        "status",
    ]
    CLUSTER_METHODS = ["scale", "adapt", "_adaptive_stop"]

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


class ClusterProcess(Process):
    """Run a dask Cluster object in a child process, and expose core methods and attributes.
    """

    def __init__(self, cluster_cls: Type[Cluster], cluster_kwargs: Optional[dict] = None):
        self.cluster_cls = cluster_cls
        self.cluster_kwargs = cluster_kwargs or {}
        # must initialize the pipes before calling `run()`
        self.__cmd_pipe = Pipe()
        self.__result_pipe = Pipe()
        super().__init__()

    @property
    def _cmd_pipe(self) -> Tuple[Connection, Connection]:
        """Pipe to receivecontrol commands from."""
        return self.__cmd_pipe

    @property
    def _result_pipe(self) -> Tuple[Connection, Connection]:
        """Pipe to return messages to."""
        return self.__result_pipe

    @property
    def cmd_conn(self) -> Connection:
        return self._cmd_pipe[1]

    @property
    def result_conn(self) -> Connection:
        return self._result_pipe[0]

    @property
    def cluster_class(self):
        class ClusterClass(self.cluster_cls):
            @property
            def num_workers(self):
                return len(self.workers)

            def _adaptive_stop(self):
                try:
                    self._adaptive.stop()
                except AttributeError:
                    pass

        return ClusterClass

    def run(self):
        if not self.cmd_conn or not self.result_conn:
            raise ValueError("Pipe are not ready!")
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

    @property
    def proxy(self) -> ClusterProcessProxy:
        """Return a proxy cluster object for controlling the cluster inside the process."""
        return ClusterProcessProxy(cmd_conn=self._cmd_pipe[0], result_conn=self._result_pipe[1])
