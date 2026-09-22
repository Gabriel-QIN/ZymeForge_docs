import asyncio

import httpx

from zymepage.app import create_app


def request(method: str, path: str, **kwargs: object) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def test_catalog_page_lists_registered_models() -> None:
    response = request("GET", "/tools")
    assert response.status_code == 200
    assert "CLEAN" in response.text
    assert "ThermoMPNN" in response.text
    assert request("GET", "/static/styles.css").status_code == 200


def test_models_api_exposes_registry_metadata() -> None:
    response = request("GET", "/api/models")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 24
    assert {model["name"] for model in payload["models"]} >= {"CLEAN", "CataPro", "GeoStab"}


def test_unknown_tool_is_404() -> None:
    assert request("GET", "/api/models/not-a-model").status_code == 404


def test_unconfigured_backend_is_explicit() -> None:
    response = request(
        "POST",
        "/api/models/clean--ec-prediction/predict",
        json={"protein_sequence": "MKTLLILAVVAALA"},
    )
    assert response.status_code == 503
    assert "weights and runner" in response.json()["detail"]
