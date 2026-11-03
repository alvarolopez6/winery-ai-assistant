import json

from scripts.sanitize_workflow import find_secrets, sanitize_workflow


def sample_workflow() -> dict:
    return {
        "id": "instance-specific",
        "name": "Demo workflow",
        "active": False,
        "pinData": {"Node": [{"json": {"secret": "value"}}]},
        "nodes": [
            {
                "id": "node-id",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "parameters": {"path": "instagram", "options": {}},
                "webhookId": "instance-webhook-id",
                "credentials": {
                    "postgres": {"id": "credential-id", "name": "Postgres account"}
                },
            }
        ],
        "connections": {},
    }


def test_sanitize_removes_instance_metadata() -> None:
    cleaned = sanitize_workflow(sample_workflow())
    assert "id" not in cleaned
    assert "pinData" not in cleaned
    node = cleaned["nodes"][0]
    assert "webhookId" not in node
    assert "id" not in node["credentials"]["postgres"]
    assert node["credentials"]["postgres"]["name"] == "Postgres account"


def test_find_secrets_detects_fake_token() -> None:
    fake = "IGAA" + "a" * 30
    workflow = {"nodes": [{"parameters": {"value": fake}}]}
    assert find_secrets(workflow)


def test_find_secrets_accepts_clean_workflow() -> None:
    assert find_secrets(sample_workflow()) == []


def test_workflow_files_are_sanitized() -> None:
    from pathlib import Path

    for path in sorted(Path("workflows").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert find_secrets(data) == [], f"possible secret in {path}"
