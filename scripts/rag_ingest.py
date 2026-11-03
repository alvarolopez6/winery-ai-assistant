"""Ingest the fictional demo documents into Qdrant.

This is the local demo path. The production path is the n8n workflow.

Usage:
    python scripts/rag_ingest.py --recreate
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from collections.abc import Iterable
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_SOURCE = Path("examples/demo")
DEFAULT_COLLECTION = "demo_wines"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "0"))  # 0 = infer from the model
BATCH_SIZE = 16


def split_text(text: str, max_chars: int = 1200, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks without cutting mid-word when possible."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be >= 0 and < max_chars")

    normalized = "\n".join(line.strip() for line in text.splitlines())
    normalized = "\n".join(line for line in normalized.splitlines() if line)
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    length = len(normalized)

    while start < length:
        end = min(start + max_chars, length)
        if end < length:
            window_start = start + max_chars // 2
            candidates = [
                normalized.rfind("\n\n", window_start, end),
                normalized.rfind("\n", window_start, end),
                normalized.rfind(". ", window_start, end),
            ]
            boundary = max(candidates)
            if boundary > start:
                end = boundary + 1

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= length:
            break

        next_start = max(end - overlap, start + 1)
        start = next_start

    return chunks


def load_documents(source: Path) -> list[tuple[str, str]]:
    """Return (source_name, chunk) pairs for every supported file."""
    if not source.exists():
        raise FileNotFoundError(f"source directory not found: {source}")

    documents: list[tuple[str, str]] = []
    for path in sorted(source.rglob("*")):
        if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for chunk in split_text(text):
            documents.append((str(path.relative_to(source)), chunk))
    return documents


def embed_texts(texts: Iterable[str], api_key: str, task_type: str) -> list[list[float]]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    embeddings: list[list[float]] = []
    batch = list(texts)

    for offset in range(0, len(batch), BATCH_SIZE):
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch[offset : offset + BATCH_SIZE],
            config=types.EmbedContentConfig(task_type=task_type),
        )
        embeddings.extend(list(embedding.values) for embedding in response.embeddings)

    if EMBEDDING_DIM:
        for vector in embeddings:
            if len(vector) != EMBEDDING_DIM:
                raise ValueError(
                    f"embedding dimension mismatch: got {len(vector)}, "
                    f"expected {EMBEDDING_DIM}. Unset EMBEDDING_DIM to infer it."
                )
    return embeddings


def point_id(source: str, index: int) -> str:
    digest = hashlib.sha256(f"{source}:{index}".encode()).hexdigest()
    return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


def ingest(source: Path, collection: str, recreate: bool) -> int:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, PointStruct, VectorParams

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    documents = load_documents(source)
    if not documents:
        raise RuntimeError(f"no .md or .txt files found in {source}")

    vectors = embed_texts(
        (chunk for _, chunk in documents),
        api_key=api_key,
        task_type="retrieval_document",
    )
    dimension = len(vectors[0])

    client = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY") or None,
        timeout=30,
    )

    if recreate and client.collection_exists(collection):
        client.delete_collection(collection)

    if not client.collection_exists(collection):
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )
    else:
        info = client.get_collection(collection)
        existing = info.config.params.vectors.size
        if existing != dimension:
            raise ValueError(
                f"collection '{collection}' has dimension {existing}, "
                f"but the model returns {dimension}. Re-run with --recreate."
            )

    points = [
        PointStruct(
            id=point_id(source_name, index),
            vector=vector,
            payload={
                "text": chunk,
                "content": chunk,
                "source": source_name,
                "metadata": {"source": source_name},
            },
        )
        for index, ((source_name, chunk), vector) in enumerate(zip(documents, vectors))
    ]

    client.upsert(collection_name=collection, points=points, wait=True)
    print(f"ingested {len(points)} chunks into '{collection}' ({dimension} dimensions)")
    return len(points)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="drop the collection before ingesting",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        ingest(args.source, args.collection, args.recreate)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
