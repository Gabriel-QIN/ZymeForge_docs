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


def test_registry_api_groups_models_and_empty_extension_points() -> None:
    response = request("GET", "/api/registries")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 8
    reaction = next(item for item in payload["registries"] if item["id"] == "reaction-mining")
    structure = next(item for item in payload["registries"] if item["id"] == "structure-search")
    function = next(item for item in payload["registries"] if item["id"] == "function-prediction")
    assert reaction["count"] == 2
    assert {tool["name"] for tool in reaction["tools"]} == {
        "Reaction-to-Enzyme Mining",
        "Substrate-to-Enzyme Mining",
    }
    assert {tool["name"] for tool in structure["tools"]} >= {
        "GraphEC-AS",
        "EC-LMGraph",
        "SaProt Retrieval",
        "ProteinMPNN Encoder Retrieval",
        "Foldseek Retrieval",
        "DALI Validation",
    }
    sequence = next(item for item in payload["registries"] if item["id"] == "sequence-search")
    assert {tool["name"] for tool in sequence["tools"]} == {"ESM-2 Retrieval"}
    assert {tool["name"] for tool in function["tools"]} >= {"CLEAN", "CataPro"}


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


def test_reaction_mining_api_uses_core_workflow() -> None:
    response = request(
        "POST",
        "/api/reactions/mine",
        json={"reaction": "CCO.O>>CC=O.O", "top_k": 2, "ph": 7.0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["reaction"]["canonical_smiles"] == "CCO.O>>CC=O.O"
    assert len(payload["candidates"]) == 2
    assert payload["candidates"][0]["score_card"]["zyme_score"] > 0


def test_reaction_mining_tool_page_uses_workflow_endpoint() -> None:
    response = request("GET", "/tools/reaction-to-enzyme--mining")
    assert response.status_code == 200
    assert 'data-endpoint="/api/reactions/mine"' in response.text


def test_substrate_and_general_reaction_discovery_apis() -> None:
    substrate = request(
        "POST",
        "/api/substrates/mine",
        json={"query": "LFQSCWFLJHTTHZ-UHFFFAOYSA-N", "top_k": 2},
    )
    reaction = request(
        "POST",
        "/api/reactions/discover",
        json={"query": "ethanol -> acetaldehyde", "top_k": 2},
    )
    assert substrate.status_code == 200
    assert reaction.status_code == 200
    assert substrate.json()["count"] == 2
    assert reaction.json()["count"] == 2
    assert substrate.json()["candidates"][0]["provenance"]["database_version"]


def test_similarity_api_reports_missing_index_without_fake_results() -> None:
    response = request(
        "POST",
        "/api/similarity/search",
        json={"query_id": "q", "sequence": "MKT", "methods": ["esm2"], "top_k": 5},
    )
    assert response.status_code == 503
    assert "ZYMEFORGE_ESM2_INDEX" in response.json()["detail"]
