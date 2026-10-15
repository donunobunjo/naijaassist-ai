
from app.services.embeddings import embed_text

sample = (
    "NaijaMobile Hub offers delivery, warranty support, "
    "and phone-buying advice."
)

vector = embed_text(sample)

print("Embedding service: PASS")
print(f"Vector dimensions: {len(vector)}")
print(f"First five values: {vector[:5]}")
