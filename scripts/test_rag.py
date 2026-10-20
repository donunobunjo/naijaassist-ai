
from app.services.rag import answer_question


def main():
    question = "What is the return policy for a phone?"

    print("Testing NaijaAssist AI RAG service...")
    print(f"Question: {question}\n")

    result = answer_question(question)

    print("ANSWER")
    print(result["answer"])

    print("\nSOURCES")
    for source in result["sources"]:
        print(f"- Title: {source['title']}")
        print(f"  Path: {source['source_path']}")
        print(f"  Chunk: {source['chunk_index']}")
        print(f"  Similarity: {source['similarity']}")
        print()


if __name__ == "__main__":
    main()
