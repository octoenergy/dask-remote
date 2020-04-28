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
    response = client.post("/scale?n=42")
    assert response.status_code == 200
    assert response.json() == {"message": "scale(42)"}

    response = client.get("/scale")
    assert response.json() == {"message": "42"}


def test_adapt(client):
    response = client.post("/adapt?minimum=0&maximum=42")
    assert response.status_code == 200
    assert response.json() == {"message": "None"}
