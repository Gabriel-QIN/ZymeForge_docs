import asyncio
import json
from pathlib import Path

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
    assert "LigandMPNN Sequence Redesign" in response.text
    assert "unZipro Mutation Prediction" in response.text
    assert "Boltz-2 Structure Prediction" in response.text
    assert "Active-site Geometry Validation" in response.text
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
    engineering = next(item for item in payload["registries"] if item["id"] == "engineering")
    structure_prediction = next(
        item for item in payload["registries"] if item["id"] == "structure-prediction"
    )
    assert reaction["count"] == 6
    assert {tool["name"] for tool in reaction["tools"]} >= {
        "Reaction-to-Enzyme Mining",
        "Substrate-to-Enzyme Mining",
        "Exact Reaction Search",
        "Reaction Similarity Search",
        "Reaction-to-EC",
        "Direct Reaction-to-Enzyme",
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
    assert {tool["name"] for tool in sequence["tools"]} == {
        "ESM-2 Retrieval",
        "TM-Vec Retrieval",
        "DHR Retrieval",
        "ProTrek Retrieval",
    }
    assert {tool["name"] for tool in function["tools"]} >= {"CLEAN", "CataPro"}
    assert {tool["name"] for tool in engineering["tools"]} >= {
        "LigandMPNN Sequence Redesign",
        "LigandMPNN Sequence Scoring",
        "unZipro Mutation Prediction",
    }
    assert {tool["name"] for tool in structure_prediction["tools"]} >= {
        "Boltz-2 Structure Prediction",
        "AlphaFold 3 Local Prediction",
        "ESMFold Fast Screening",
        "MolProbity Structure QC",
    }
    evidence = next(item for item in payload["registries"] if item["id"] == "evidence-fusion")
    output = next(item for item in payload["registries"] if item["id"] == "output")
    assert {tool["name"] for tool in evidence["tools"]} >= {
        "Weighted Evidence Fusion",
        "Reciprocal Rank Fusion",
        "ZymeScore Candidate Ranking",
    }
    assert {tool["name"] for tool in output["tools"]} >= {
        "JSON Result Writer",
        "Candidate TSV Writer",
        "Harness Run Artifacts",
    }


def test_static_registry_snapshot_matches_live_catalog() -> None:
    snapshot = json.loads(
        Path("docs/data/registry_snapshot.json").read_text(encoding="utf-8")
    )
    live = request("GET", "/api/registries").json()["registries"]
    assert snapshot["registries"] == live
    assert all(group["count"] > 0 for group in live)


def test_engineering_tool_pages_use_dedicated_endpoints() -> None:
    redesign = request("GET", "/tools/ligandmpnn--sequence-redesign")
    mutation = request("GET", "/tools/unzipro--mutation-prediction")
    assert redesign.status_code == 200
    assert 'data-endpoint="/api/engineering/redesign"' in redesign.text
    assert mutation.status_code == 200
    assert 'data-endpoint="/api/engineering/mutations"' in mutation.text


def test_engineering_api_reports_missing_official_backend() -> None:
    structure = "ATOM      1  N   ALA A   1      0.000   0.000   0.000"
    redesign = request(
        "POST",
        "/api/engineering/redesign",
        json={"structure_pdb": structure, "model_type": "protein_mpnn"},
    )
    mutation = request(
        "POST",
        "/api/engineering/mutations",
        json={
            "parent_id": "p1",
            "sequence": "A",
            "structure_pdb": structure,
            "top_k": 1,
        },
    )
    assert redesign.status_code == 503
    assert "ZYMEFORGE_LIGANDMPNN_SOURCE" in redesign.json()["detail"]
    assert mutation.status_code == 503
    assert "ZYMEFORGE_UNZIPRO_SOURCE" in mutation.json()["detail"]


def test_structure_catalog_and_missing_provider_are_explicit() -> None:
    page = request("GET", "/tools/boltz2--structure-prediction")
    assert page.status_code == 200
    assert 'data-endpoint="/api/structures/predict"' in page.text
    response = request(
        "POST",
        "/api/structures/predict",
        json={"candidate_id": "c1", "method": "boltz2", "sequence": "ACDE"},
    )
    assert response.status_code == 503
    assert "Boltz-2" in response.json()["detail"]


def test_structure_api_rejects_client_paths() -> None:
    response = request(
        "POST",
        "/api/structures/predict",
        json={
            "candidate_id": "c1",
            "method": "boltz2",
            "sequence": "ACDE",
            "options": {"cache": "/tmp/server"},
        },
    )
    assert response.status_code == 422
    assert "server-managed" in response.json()["detail"]


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
    tmvec = request(
        "POST",
        "/api/similarity/search",
        json={"query_id": "q", "sequence": "MKT", "methods": ["tmvec"], "top_k": 5},
    )
    assert tmvec.status_code == 503
    assert "ZYMEFORGE_TMVEC_INDEX" in tmvec.json()["detail"]


def test_harness_page_and_waiting_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZYMEFORGE_HARNESS_RUNS", str(tmp_path))
    page = request("GET", "/harness")
    assert page.status_code == 200
    assert "From scientific intent" in page.text
    agent_request = {
        "task_type": "remote_homology",
        "target": {},
        "constraints": {"max_sequence_identity": 0.3},
        "objectives": ["novelty"],
        "output_requirements": {"top_n": 20},
        "steps": [
            {
                "step_id": "S1",
                "capability": "remote_homology_search",
                "depends_on": [],
                "parameters": {},
            }
        ],
        "missing_information": ["query protein sequence"],
    }
    created = request(
        "POST",
        "/api/harness/run",
        json={"query": "Find remote homologs", "agent_request": agent_request},
    )
    assert created.status_code == 200
    status = request("GET", f"/api/harness/runs/{created.json()['run_id']}")
    assert status.status_code == 200
    assert status.json()["status"] == "WAITING_FOR_INPUT"
    assert status.json()["candidate_count"] == 0


def test_harness_api_rejects_server_paths() -> None:
    response = request(
        "POST",
        "/api/harness/run",
        json={
            "query": "Search this structure",
            "agent_request": {
                "task_type": "structure_search",
                "target": {"structure_file": "/etc/passwd"},
                "constraints": {},
                "objectives": ["structure_similarity"],
                "output_requirements": {"top_n": 10},
                "steps": [
                    {
                        "step_id": "S1",
                        "capability": "structure_similarity",
                        "depends_on": [],
                        "parameters": {},
                    }
                ],
                "missing_information": [],
            },
        },
    )
    assert response.status_code == 422
    assert "filesystem paths" in response.json()["detail"]
