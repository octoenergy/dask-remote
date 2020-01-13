def pytest_addoption(parser):
    parser.addoption("--host", default="localhost", help="Hostname of a running scheduler")
    parser.addoption("--port", default="30321", help="Scheduler port")
    parser.addoption("--dashboard-port", default="30787", help="Dashboard port")
    parser.addoption("--namespace", default="test", help="Worker deployment namespace")
    parser.addoption("--deployment", default="dask-worker", help="Worker deployment name")
