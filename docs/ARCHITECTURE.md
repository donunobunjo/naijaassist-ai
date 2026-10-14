# Architecture Notes

## Data ownership
| Information | Source of truth | Use of RAG |
|---|---|---|
| Current price | `product_prices` | Not authoritative; do not rely on embedded prices |
| Price history | `product_price_history` | None required |
| Stock | `inventory` | Not authoritative |
| Product specs/condition | `products` | Descriptive content may be retrieved, but verify exact fields in SQL |
| Handbook/policies/FAQ | Approved Markdown documents | Yes, after ingestion and approval |
| Conversation history | `messages` | Recent messages can be selected as context under limits |
| Customer preferences | `customer_memories` | Only selected, non-sensitive, unexpired facts |
| Order/payment status | Future trusted integration | Never infer from conversation |

## Price freshness
The initial rule considers a price fresh when `updated_at` is no more than seven days old and is not in the future. A valid timestamp is necessary, not sufficient: status must also be `approved`, and the record must come from the trusted database.

## Embedding dimension
The initial schema uses `VECTOR(384)` to match `sentence-transformers/all-MiniLM-L6-v2`. If the embedding model changes, update the schema and re-embed all indexed content consistently.

## Reliability and security
- Verify webhook signatures before parsing or acting on incoming messages.
- Make webhook processing idempotent.
- Use parameterized SQL and narrow application tools.
- Apply authentication and authorization to administrative operations.
- Avoid storing secrets in the repository.
- Apply timeouts, bounded retries, and observability to external API calls.
- Treat all customer content and retrieved documents as untrusted data.
