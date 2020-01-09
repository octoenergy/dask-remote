# dask-remote
Provides a kubernetes-native `dask` distributed cluster deployment.

The project is heavily inspired by, but takes a different approach to, `dask-kubernetes`.

## Usage
- see `kubernetes/deployment.yaml` for a sample deployment - use `kubectl`/`helm`/...
- instantiate a `DeploymentCluster`, e.g.:
```python
cluster = DeploymentCluster(
    remote_scheduler="tcp://scheduler.test:54321",
    deployment_name="dask-worker",
    namespace="test",
    in_cluster=True ,  # if running inside the K8S cluster
    config_file="..."  # if authenticating with a K8s cluster using a config file
)
```
The cluster now provides the expected `scale` functionality, and can be passed to a `Client` for
submitting computations.

## Background
Instead of relying on `SpecCluster`, the `DeploymentCluster` provides a *stateless* cluster implementation that relies on a `Deployment` kubernetes resource type for scaling a worker group.

- ✔️ our approach simplifies deployment and allows adding the `DeploymentCluster` to an existing deployment
- ✔️ the size of the worker pool is maintained in the presence of pod evictions, node failures, and other chaos events
- ❌ on the flip side, the stateless cluster approach is currently unable to handle "graceful"
worker shut-down or selecting specific workers/Pods to close.

## Testing
Tests assume the deployment is created locally with `minikube`.

Run `make k8s-apply` to create a local deployment, followed by `make test` to run tests.
The test suite can be run against a deployment with a different hostname/port by passing
the following options to `pytest`:
- `--host`: host name or IP (defaults to `localhost`, or `$(minikube ip)` if run from the Makefile
- `--port`: scheduler port, defaults to the exposed NodePort 30321
- `--dashboard-port`: scheduler port, defaults to the exposed NodePort 30787
