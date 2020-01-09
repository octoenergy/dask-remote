import asyncio

import pytest

from dask_remote import DeploymentCluster


@pytest.fixture
async def cluster(scheduler_address, namespace, deployment):
    async with DeploymentCluster(
        scheduler_address, deployment, namespace=namespace, asynchronous=True
    ) as cluster:
        yield cluster


@pytest.mark.asyncio
async def test_cluster(cluster):
    info = cluster.scheduler_info
    assert info["type"] == "Scheduler"


@pytest.mark.asyncio
@pytest.mark.parametrize("n", [1, 0])
async def test_scaling(cluster, n):
    MAX_TIMEOUT = 20
    await cluster.scale(n)
    for _ in range(MAX_TIMEOUT):
        if len(cluster.workers) == n:
            break
        await asyncio.sleep(1)
    else:
        raise AssertionError(f"Failed to scale to {n} workers in under {MAX_TIMEOUT}s")
