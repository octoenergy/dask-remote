# `dask_remote.runner`

- `ClusterProcess` provides a way to run any `Cluster` in a python process, thus allowing easy way to build CLIs and other non-interactive cluster deployments
- `ClusterProcessProxy` provides a process and thread-safe for each `ClusterProcess` to allow access to methods and attributes such as `scale`
- `dask_remote.runner.api` provides a way to expose the proxy methods via a RESTful API built on `FastAPI`, as well as a way to run a simple `uvicorn` server exposing this API in a separate process.

## Example

A combined example:

```python
from multiprocessing import Pipe

from dask.distributed import LocalCluster
from dask_remote.runner import ClusterProcess, ClusterProcessProxy, ApiProcess

cmd_conn, result_conn = Pipe()

cluster_proc = ClusterProcess(cmd_conn, result_conn, LocalCluster, dict(n_workers=0))
cluster_proc.start()  # uses the multiprocessing.Process API

cluster_proxy = ClusterProcessProxy(cmd_conn, result_conn)
cluster_proxy.scale(4)  # command is proxied to the cluster object in the child process

api_proc = ApiProcess(cluster_proxy)

cluster_proc.join()  # cluster remains alive until terminated
api_proc.join()
```

With the API server running, you can see API docs on `http://localhost:8000/docs`.
E.g. you can scale the claster using

```
$ curl -X POST http://localhost:8000/scale/42
```

## ToDo

- add a client for this API
- auto-generate Pipes for a Process-Proxy pair
