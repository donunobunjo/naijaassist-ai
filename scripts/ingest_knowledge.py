
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

from app.config import settings
from app.services.embeddings import embed_text

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge_base"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
EMBEDDING_DELAY_SECONDS = 0.2


def split_text(text: str) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph boundaries."""
    text = re.sub(r"\r\n?", "\n", text).strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))

        if end < len(text):
            boundary = text.rfind("\n\n", start, end)
            if boundary > start + CHUNK_SIZE // 2:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        next_start = max(start + 1, end - CHUNK_OVERLAP)
        start = next_start

    return chunks


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    if not KNOWLEDGE_DIR.is_dir():
        raise FileNotFoundError(
            f"Knowledge-base directory not found: {KNOWLEDGE_DIR}"
        )

    documents = sorted(KNOWLEDGE_DIR.glob("*.md"))

    if not documents:
        raise FileNotFoundError(
            f"No Markdown files found in {KNOWLEDGE_DIR}"
        )

    print(f"Found {len(documents)} Markdown documents.")

    # Generate embeddings before opening the database transaction.
    prepared_documents = []

    for file_path in documents:
        content = file_path.read_text(encoding="utf-8").strip()

        if not content:
            print(f"Skipping empty document: {file_path.name}")
            continue

        chunks = split_text(content)
        content_hash = sha256_text(content)

        print(f"Preparing {file_path.name}: {len(chunks)} chunks")

        embeddings = []

        for index, chunk in enumerate(chunks):
            vector = embed_text(chunk, task_type="RETRIEVAL_DOCUMENT")

            if len(vector) != 768:
                raise ValueError(
                    f"{file_path.name}, chunk {index}: "
                    f"expected 768 dimensions, got {len(vector)}"
                )

            embeddings.append(vector)

            if index < len(chunks) - 1:
                time.sleep(EMBEDDING_DELAY_SECONDS)

        prepared_documents.append(
            {
                "source_path": file_path.relative_to(ROOT).as_posix(),
                "title": file_path.stem.replace("_", " ").title(),
                "content_hash": content_hash,
                "chunks": chunks,
                "embeddings": embeddings,
            }
        )

    if not prepared_documents:
        print("No non-empty documents to ingest.")
        return

    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)

        with conn.cursor() as cur:
            for document in prepared_documents:
                cur.execute(
                    """
                    SELECT id, content_hash
                    FROM knowledge_documents
                    WHERE source_path = %s
                    FOR UPDATE
                    """,
                    (document["source_path"],),
                )

                existing = cur.fetchone()

                if (
                    existing
                    and existing[1] == document["content_hash"]
                ):
                    # The content is unchanged. Ensure it remains approved
                    # because this script ingests only curated local files.
                    cur.execute(
                        """
                        UPDATE knowledge_documents
                        SET approved = TRUE,
                            title = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (document["title"], existing[0]),
                    )
                    print(
                        f"Unchanged: {document['source_path']} "
                        "(existing chunks retained)"
                    )
                    continue

                if existing:
                    document_id = existing[0]

                    cur.execute(
                        """
                        UPDATE knowledge_documents
                        SET title = %s,
                            content_hash = %s,
                            approved = TRUE,
                            version = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (
                            document["title"],
                            document["content_hash"],
                            document["content_hash"][:12],
                            document_id,
                        ),
                    )

                    cur.execute(
                        """
                        DELETE FROM document_chunks
                        WHERE document_id = %s
                        """,
                        (document_id,),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO knowledge_documents (
                            source_path,
                            title,
                            content_hash,
                            approved,
                            version
                        )
                        VALUES (%s, %s, %s, TRUE, %s)
                        RETURNING id
                        """,
                        (
                            document["source_path"],
                            document["title"],
                            document["content_hash"],
                            document["content_hash"][:12],
                        ),
                    )

                    document_id = cur.fetchone()[0]

                for index, (chunk, vector) in enumerate(
                    zip(document["chunks"], document["embeddings"])
                ):
                    metadata = {
                        "source_path": document["source_path"],
                        "title": document["title"],
                    }

                    cur.execute(
                        """
                        INSERT INTO document_chunks (
                            document_id,
                            chunk_index,
                            content,
                            embedding,
                            metadata
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            document_id,
                            index,
                            chunk,
                            vector,
                            json.dumps(metadata),
                        ),
                    )

                print(
                    f"Ingested: {document['source_path']} "
                    f"({len(document['chunks'])} chunks)"
                )

        # The connection context commits if everything succeeds.
        # An exception causes the transaction to roll back.

    print("Knowledge-base ingestion completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Ingestion failed: {type(exc).__name__}: {exc}")
        sys.exit(1)
