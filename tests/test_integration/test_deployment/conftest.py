import pytest


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
