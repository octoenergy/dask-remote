import pytest


def pytest_addoption(parser):
    parser.addoption("--host", default="localhost", help="Hostname of a running scheduler")
    parser.addoption("--port", default="30321", help="Scheduler port")
    parser.addoption("--dashboard-port", default="30787", help="Dashboard port")
    parser.addoption("--namespace", default="test", help="Worker deployment namespace")
    parser.addoption("--deployment", default="dask-worker", help="Worker deployment name")


@pytest.fixture
def scheduler_address(request):
    host = request.config.getoption("--host")
    port = request.config.getoption("--port")
    return f"tcp://{host}:{port}"


@pytest.fixture
def dashboard_address(request):
    host = request.config.getoption("--host")
    port = request.config.getoption("--dashboard-port")
    return f"http://{host}:{port}"


@pytest.fixture
def namespace(request):
    return request.config.getoption("--namespace")


@pytest.fixture
def deployment(request):
    return request.config.getoption("--deployment")
