
from app.services.retrieval import retrieve_context
from app.services.llm import generate_answer


def answer_question(question: str, limit: int = 5) -> dict:
    """
    Retrieve relevant knowledge, generate an answer, and return sources.
    """

    if not question or not question.strip():
        return {
            "answer": "Please enter a question.",
            "sources": [],
        }

    # Step 1: Retrieve relevant knowledge-base passages.
    chunks = retrieve_context(question.strip(), limit=limit)

    # Step 2: If retrieval finds nothing, do not ask the LLM to guess.
    if not chunks:
        return {
            "answer": (
                "I couldn't find enough information in our approved "
                "knowledge base to answer that confidently. "
                "Please contact our support team for confirmation."
            ),
            "sources": [],
        }

    # Step 3: Prepare the retrieved passages for the LLM.
    context_parts = []

    for chunk in chunks:
        context_parts.append(
            f"Source: {chunk['title']}\n"
            f"Document path: {chunk['source_path']}\n"
            f"Content:\n{chunk['content']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    # Step 4: Generate an answer grounded in the retrieved passages.
    answer = generate_answer(
        question=question.strip(),
        context=context,
    )

    # Step 5: Return source references with the answer.
    sources = [
        {
            "title": chunk["title"],
            "source_path": chunk["source_path"],
            "chunk_index": chunk["chunk_index"],
            "similarity": chunk["similarity"],
        }
        for chunk in chunks
    ]

    return {
        "answer": answer,
        "sources": sources,
    }
