# Escalation Procedures — Demo Version

Escalate when any of these conditions occur:
- The customer explicitly asks for a human.
- Price, stock, warranty, delivery, payment, or policy records are missing, stale, or contradictory.
- A return, refund, warranty, or legal-rights decision requires judgment.
- Payment cannot be verified by the trusted system.
- The customer reports fraud, account compromise, safety concerns, or a serious complaint.
- The assistant has failed to resolve the request after two clear attempts.
- A request requires a privileged operation or access to data the assistant is not authorized to retrieve.

## Handoff sequence
1. Explain briefly why a human review is appropriate.
2. Create a ticket using the approved support workflow.
3. Confirm ticket creation and notification status from tool results.
4. Tell the customer what actually succeeded and provide a reference only if one exists.
5. If notification fails, do not say a human has been notified; explain the limitation and offer the approved alternative.

## Priority guidance
- Urgent: credible account/payment compromise or immediate safety issue.
- High: suspected fraud, repeated payment discrepancy, serious complaint.
- Normal: return/warranty review, delivery issue, unresolved product question.
- Low: general feedback or non-urgent product inquiry.
