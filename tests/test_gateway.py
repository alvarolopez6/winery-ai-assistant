import hashlib
import hmac

import httpx
from fastapi.testclient import TestClient

from gateway.app import Settings, create_app


def make_app(configured: bool = True):
    calls: list[tuple[bytes, dict[str, str]]] = []
    settings = Settings(
        app_secret="app-secret" if configured else "",
        verify_token="verify-token" if configured else "",
        n8n_url="http://n8n:5678/webhook/instagram",
    )

    async def fake_forward(body: bytes, headers: dict[str, str]) -> httpx.Response:
        calls.append((body, headers))
        return httpx.Response(
            200,
            content=b'{"ok":true}',
            headers={"content-type": "application/json"},
        )

    return TestClient(create_app(settings, fake_forward)), calls


def sign(body: bytes, secret: str = "app-secret") -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_healthz_when_configured() -> None:
    client, _ = make_app()
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_healthz_when_misconfigured() -> None:
    client, _ = make_app(configured=False)
    response = client.get("/healthz")
    assert response.status_code == 503


def test_get_verification_returns_challenge() -> None:
    client, _ = make_app()
    response = client.get(
        "/webhook/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-token",
            "hub.challenge": "challenge-value",
        },
    )
    assert response.status_code == 200
    assert response.text == "challenge-value"


def test_get_verification_rejects_wrong_token() -> None:
    client, _ = make_app()
    response = client.get(
        "/webhook/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "challenge-value",
        },
    )
    assert response.status_code == 403


def test_post_forwards_valid_signature() -> None:
    client, calls = make_app()
    body = b'{"object":"instagram","entry":[]}'
    response = client.post(
        "/webhook/instagram",
        content=body,
        headers={
            "content-type": "application/json",
            "x-hub-signature-256": sign(body),
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert len(calls) == 1
    assert calls[0][0] == body


def test_post_rejects_invalid_signature_without_forwarding() -> None:
    client, calls = make_app()
    body = b'{"object":"instagram"}'
    response = client.post(
        "/webhook/instagram",
        content=body,
        headers={
            "content-type": "application/json",
            "x-hub-signature-256": "sha256=deadbeef",
        },
    )
    assert response.status_code == 403
    assert calls == []


def test_post_rejects_missing_signature() -> None:
    client, calls = make_app()
    response = client.post(
        "/webhook/instagram",
        content=b"{}",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 403
    assert calls == []
