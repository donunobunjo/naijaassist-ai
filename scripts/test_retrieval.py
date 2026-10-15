
from app.services.retrieval import retrieve_context

questions = [
    "What is the policy for returning a phone?",
    "How can I get help with a warranty claim?",
    "What should the assistant do if a price is unverified?",
]

for question in questions:
    print("\n" + "=" * 70)
    print(f"QUESTION: {question}")

    results = retrieve_context(question, limit=3)

    if not results:
        print("No matching approved passages found.")
        continue

    for index, result in enumerate(results, start=1):
        print(f"\nResult {index}")
        print(f"Document: {result['title']}")
        print(f"Chunk: {result['chunk_index']}")
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Content: {result['content'][:350]}")
