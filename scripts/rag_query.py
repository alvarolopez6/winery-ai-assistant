"""Ask a question against the local demo RAG collection.

This bypasses Instagram and n8n so reviewers can try the retrieval pipeline
without a Meta developer account.

Usage:
    python scripts/rag_query.py "¿Qué vino recomiendas para una barbacoa?"
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

DEFAULT_COLLECTION = "demo_wines"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.5-flash")

SYSTEM_PROMPT = """Eres el asistente virtual de una bodega ficticia de demostración.
Responde únicamente con la información del contexto proporcionado.
No inventes precios, horarios ni disponibilidad.
Si el contexto no contiene la respuesta, di: "No tengo ese dato; te derivaré a una persona del equipo."
Responde en español, de forma breve y profesional."""


def embed_question(question: str, api_key: str) -> list[float]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return list(response.embeddings[0].values)


def retrieve(question: str, collection: str, top_k: int) -> list[dict]:
    from qdrant_client import QdrantClient

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY") or None,
        timeout=30,
    )
    if not client.collection_exists(collection):
        raise RuntimeError(
            f"collection '{collection}' does not exist. "
            "Run: python scripts/rag_ingest.py --recreate"
        )

    vector = embed_question(question, api_key)
    response = client.query_points(
        collection_name=collection,
        query=vector,
        limit=top_k,
        with_payload=True,
    )
    return [
        {
            "score": round(point.score, 4),
            "source": (point.payload or {}).get("source", "unknown"),
            "text": (point.payload or {}).get("text", ""),
        }
        for point in response.points
    ]


def answer(question: str, chunks: list[dict]) -> str:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)
    context = "\n\n".join(
        f"[{index + 1}] {chunk['source']}\n{chunk['text']}"
        for index, chunk in enumerate(chunks)
    )
    prompt = f"{SYSTEM_PROMPT}\n\nContexto:\n{context}\n\nPregunta: {question}"
    response = client.models.generate_content(model=CHAT_MODEL, contents=prompt)
    return response.text.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="question to ask the demo assistant")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--json", action="store_true", help="print machine-readable output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        chunks = retrieve(args.question, args.collection, args.top_k)
        reply = answer(args.question, chunks)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"answer": reply, "sources": chunks}, ensure_ascii=False, indent=2))
    else:
        print(reply)
        print("\nFuentes:")
        for index, chunk in enumerate(chunks, start=1):
            print(f"  [{index}] {chunk['source']} (score={chunk['score']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
