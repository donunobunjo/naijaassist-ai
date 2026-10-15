
from app.services.price_answer import answer_price_question

test_questions = [
    "Samsung Galaxy A04",
    "NMH-PHN-0016",
    "Samsung",
    "a product name that does not exist",
    "",
]

for question in test_questions:
    print("\n" + "=" * 60)
    print(f"Customer query: {question!r}")

    try:
        answer = answer_price_question(question)
        print(f"Assistant: {answer}")
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
