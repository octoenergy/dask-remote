import requests


def test_dashboard_is_up(dashboard_address):
    """Check that the minikube test deployment is available.

    The host IP will be set automatically from `minikube ip`
    if the test suite is run from `make test`.
    """
    response = requests.get(f"{dashboard_address}/health")
    assert response.status_code == 200
    assert response.text == "ok"
