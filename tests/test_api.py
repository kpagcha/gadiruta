from django.test import Client


def test_health_is_available_without_a_database(client: Client) -> None:
    # pytest-django blocks database access unless a test explicitly requests it.
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_rejects_writes(client: Client) -> None:
    assert client.post("/api/v1/health").status_code == 405


def test_openapi_describes_health_response(client: Client) -> None:
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Gadiruta API"
    operation = schema["paths"]["/api/v1/health"]["get"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }
    assert (
        schema["components"]["schemas"]["HealthResponse"]["properties"]["status"]["const"] == "ok"
    )


def test_interactive_docs_are_available(client: Client) -> None:
    response = client.get("/api/v1/docs")

    assert response.status_code == 200
    assert b"/api/v1/openapi.json" in response.content
