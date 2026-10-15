
from app.services.llm import generate_answer


question = "What is the return policy for a phone?"

context = """
Source: Returns Refunds

This is a fictional portfolio demonstration policy.
An eligible return request should initially be raised within
seven calendar days of the recorded delivery date.
Do not automatically reject a complaint if this period has passed.
Escalate exceptions for review.
"""


print("Testing NaijaAssist AI LLM service...")
print(f"Question: {question}")
print("\nGenerating answer...\n")

try:
    answer = generate_answer(
        question=question,
        context=context,
    )
    print("Assistant answer:")
    print(answer)

except Exception as exc:
    print(f"ERROR: {type(exc).__name__}: {exc}")
