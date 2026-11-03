"""Public webhook gateway for Instagram/Meta.

Meta needs two things from the public endpoint:

1. A GET challenge for webhook verification.
2. A POST endpoint that verifies X-Hub-Signature-256 before forwarding.

n8n stays private behind this gateway.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

DEFAULT_N8N_URL = "http://n8n:5678/webhook/instagram"


@dataclass(frozen=True)
class Settings:
    app_secret: str
    verify_token: str
    n8n_url: str = DEFAULT_N8N_URL
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            app_secret=os.getenv("INSTAGRAM_APP_SECRET", ""),
            verify_token=os.getenv("INSTAGRAM_VERIFY_TOKEN", ""),
            n8n_url=os.getenv("N8N_INTERNAL_WEBHOOK_URL", DEFAULT_N8N_URL),
            timeout=float(os.getenv("FORWARD_TIMEOUT", "30")),
        )

    @property
    def configured(self) -> bool:
        return bool(self.app_secret and self.verify_token)


Forwarder = Callable[[bytes, dict[str, str]], Awaitable[httpx.Response]]


def verify_signature(secret: str, body: bytes, signature: str | None) -> bool:
    """Validate Meta's X-Hub-Signature-256 header."""
    if not secret or not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, f"sha256={expected}")


async def forward_to_n8n(
    settings: Settings, body: bytes, headers: dict[str, str]
) -> httpx.Response:
    async with httpx.AsyncClient(timeout=settings.timeout) as client:
        return await client.post(
            settings.n8n_url,
            content=body,
            headers={"content-type": headers.get("content-type", "application/json")},
        )


def create_app(settings: Settings | None = None, forwarder: Forwarder | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(
        title="Instagram Webhook Gateway",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    async def default_forward(body: bytes, headers: dict[str, str]) -> httpx.Response:
        return await forward_to_n8n(settings, body, headers)

    forward = forwarder or default_forward

    @app.get("/healthz")
    async def healthz() -> Response:
        if not settings.configured:
            return JSONResponse({"status": "misconfigured"}, status_code=503)
        return JSONResponse({"status": "ok"})

    @app.get("/webhook/instagram")
    async def verify_webhook(request: Request) -> Response:
        params = request.query_params
        if params.get("hub.mode") != "subscribe":
            return PlainTextResponse("forbidden", status_code=403)
        token = params.get("hub.verify_token", "")
        if not settings.verify_token or not hmac.compare_digest(token, settings.verify_token):
            return PlainTextResponse("forbidden", status_code=403)
        challenge = params.get("hub.challenge")
        if not challenge:
            return PlainTextResponse("missing challenge", status_code=400)
        return PlainTextResponse(challenge)

    @app.post("/webhook/instagram")
    async def receive_webhook(request: Request) -> Response:
        if not settings.configured:
            return JSONResponse({"error": "gateway is not configured"}, status_code=503)

        body = await request.body()
        signature = request.headers.get("x-hub-signature-256")
        if not verify_signature(settings.app_secret, body, signature):
            return JSONResponse({"error": "invalid signature"}, status_code=403)

        try:
            upstream = await forward(body, dict(request.headers))
        except httpx.HTTPError as exc:
            return JSONResponse(
                {"error": "upstream unavailable", "detail": str(exc)},
                status_code=502,
            )

        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers={
                "content-type": upstream.headers.get("content-type", "application/json")
            },
        )

    return app


app = create_app()
