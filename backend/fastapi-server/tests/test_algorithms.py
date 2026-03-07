from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models.algorithm import Algorithm


def test_list_algorithms_empty(client: TestClient):
    response = client.get("/api/v1/algorithms/")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0


def test_get_algorithm_not_found(client: TestClient):
    response = client.get("/api/v1/algorithms/999")
    assert response.status_code == 404


def test_get_algorithm_by_slug_not_found(client: TestClient):
    response = client.get("/api/v1/algorithms/by-slug/nonexistent")
    assert response.status_code == 404


def test_list_algorithms_with_data(client: TestClient, session: Session):
    algorithm = Algorithm(
        name="Linear Regression",
        slug="linear-regression",
        category="supervised",
        subcategory="regression",
        complexity="low",
    )
    session.add(algorithm)
    session.commit()

    response = client.get("/api/v1/algorithms/")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1
    assert data["data"][0]["slug"] == "linear-regression"
