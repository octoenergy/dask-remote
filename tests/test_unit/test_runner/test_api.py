import pytest
from starlette.testclient import TestClient

MAX_TIMEOUT = 10


@pytest.fixture
def client(api_app):
    return TestClient(api_app)


def test_status(client):
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"message": "running"}


def test_scale(client):
    response = client.post("/scale/42")
    assert response.status_code == 200
    assert response.json() == {"message": "Scaling to 42 workers"}

    response = client.get("/scale")
    assert response.json() == {"message": "42"}
