# Test Plan

## Price correctness
- Approved fresh price is quoted exactly from SQL.
- Pending/retired price is not quoted as current.
- Price older than configured freshness threshold is flagged stale.
- Missing or future timestamp is not silently accepted.
- Price update creates history record.
- Import with invalid price, duplicate SKU, or unknown SKU fails atomically.
- Price import never changes inventory.

## Catalogue and inventory
- Unknown SKU produces a clear not-found result.
- Inactive products are not recommended.
- Zero stock is reported as out of stock.
- Missing/stale inventory produces an unconfirmed status.

## RAG and groundedness
- Policy answers cite/use approved sources.
- Unsupported questions trigger clarification or abstention.
- Conflicting policies trigger escalation.
- Prompt injection in customer content does not override business rules.
- Routine price changes do not require re-embedding.

## WhatsApp integration
- Invalid webhook signature is rejected.
- Duplicate provider message ID is processed once.
- Outbound API failures are retried safely and do not duplicate messages.
- A human handoff is only reported as complete after successful ticket/notification result.

## Privacy and security
- Secrets are not returned by health/debug endpoints or written to logs.
- Customer A cannot access Customer B's conversation or order.
- Memory expires and can be corrected/deleted.
- Retention jobs honor configured periods.
