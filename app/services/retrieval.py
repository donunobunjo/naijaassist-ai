
import psycopg
from pgvector.psycopg import register_vector

from app.config import settings
from app.services.embeddings import embed_text


def retrieve_context(
    question: str,
    limit: int = 5,
) -> list[dict]:
    """Retrieve the most relevant chunks from approved documents."""

    if not question or not question.strip():
        return []

    if not 1 <= limit <= 10:
        raise ValueError("limit must be between 1 and 10.")

    # Embed the customer's question using the same model and dimensions
    # used to embed the knowledge-base documents.
    question_vector = embed_text(
        question,
        task_type="RETRIEVAL_QUERY",
    )

    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    kd.title,
                    kd.source_path,
                    dc.chunk_index,
                    dc.content,
                    1 - (dc.embedding <=> %s::vector) AS similarity
                FROM document_chunks AS dc
                JOIN knowledge_documents AS kd
                    ON kd.id = dc.document_id
                WHERE kd.approved = TRUE
                  AND dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> %s::vector
                LIMIT %s
                """,
                (question_vector, question_vector, limit),
            )

            rows = cur.fetchall()

    return [
        {
            "title": row[0],
            "source_path": row[1],
            "chunk_index": row[2],
            "content": row[3],
            "similarity": float(row[4]) if row[4] is not None else None,
        }
        for row in rows
    ]
