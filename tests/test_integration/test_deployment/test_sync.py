import time

import pytest

from dask_remote.deployment import DeploymentCluster


@pytest.fixture
def cluster(scheduler_address, namespace, deployment):
    with DeploymentCluster(scheduler_address, deployment, namespace=namespace) as cluster:
        yield cluster


def test_cluster(cluster):
    info = cluster.scheduler_info
    assert info["type"] == "Scheduler"


@pytest.mark.parametrize("n", [1, 0])
def test_scaling(cluster, n):
    MAX_TIMEOUT = 20
    cluster.scale(n)
    for _ in range(MAX_TIMEOUT):
        if len(cluster.workers) == n:
            break
        time.sleep(1)
    else:
        raise AssertionError(f"Failed to scale to {n} workers in under {MAX_TIMEOUT}s")
