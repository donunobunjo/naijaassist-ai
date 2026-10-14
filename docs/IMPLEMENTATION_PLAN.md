# Implementation Plan

## Milestone 1 — Foundation (current starter)
- [x] Project structure and environment template
- [x] Synthetic product/price/inventory CSVs
- [x] PostgreSQL schema with pgvector
- [x] Transactional CSV importer with validation
- [x] Price freshness assessment function
- [x] Basic FastAPI health and webhook-verification endpoints
- [x] Demo policies and buying guide
- [ ] Run schema/import against a real PostgreSQL+pgvector database
- [ ] Expand automated tests for importer and database integration

## Milestone 2 — WhatsApp transport
- Validate `X-Hub-Signature-256` against raw request bytes and Meta app secret.
- Normalize inbound webhook events.
- Deduplicate events with `webhook_events` and provider message IDs.
- Persist customer, conversation, and inbound message records.
- Add outbound WhatsApp Cloud API client with timeouts, retries, and safe logging.
- Test delivery/read/error webhook statuses.
- Do not log tokens or unnecessary message content.

## Milestone 3 — RAG ingestion and retrieval
- Read only approved knowledge-base documents.
- Chunk documents and preserve source path, title, version, and chunk index.
- Embed with the configured 384-dimensional model and store in pgvector.
- Add retrieval filtering for approved documents.
- Return source metadata internally; test retrieval quality.
- Never treat embedded price text as authoritative.

## Milestone 4 — Agent and tools
- Add explicit request classification/routing.
- Implement narrow parameterized tools for product lookup, price, stock, order status, and ticket creation.
- Add policy retrieval and grounded answer generation.
- Add abstention, clarification, prompt-injection defenses, and human handoff.
- Keep model-generated text separate from privileged application actions.

## Milestone 5 — Admin and data governance
- Add authenticated/authorized price and inventory update endpoints.
- Record who changed what, when, and why.
- Add approval workflow for price changes and promotions.
- Add retention, correction, deletion, consent, and audit controls.
- Add a human support queue and handoff notifications.

## Milestone 6 — Evaluation and deployment
- Curate 100–150 expected-answer test cases.
- Measure exact-price correctness, stock correctness, retrieval Recall@k/MRR, groundedness, handoff correctness, and latency.
- Test duplicate webhooks, model/API failures, stale prices, conflicting sources, and prompt injection.
- Deploy API and database with secret management, HTTPS, logs, monitoring, and backups.
- Verify current provider free-tier limits; zero-cost operation is not guaranteed.
