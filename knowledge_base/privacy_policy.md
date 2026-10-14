# Privacy Notice — Demo Draft

**This is a development draft for a fictional service, not legal advice or a final compliance document. Obtain appropriate privacy/legal review before any real deployment.**

NaijaMobile AI is designed to process only information needed to answer a customer request and manage support.

## Data potentially processed
- WhatsApp/provider customer identifier and phone number.
- Messages, timestamps, conversation status, and support ticket details.
- Product preferences explicitly provided by the customer.
- Technical event identifiers required to prevent duplicate webhook processing.

## Data minimization
Do not store passwords, OTPs, PINs, CVVs, or unnecessary sensitive information. Do not convert every message into permanent customer memory. Keep selected memory separate from message history and expire it.

## Access, correction, and deletion
A real deployment should provide a documented way to request access, correction, or deletion, subject to applicable requirements and legitimate retention obligations.

## Retention
The initial project defaults (90 days for raw conversation content and 180 days for selected preferences or resolved tickets) are configurable engineering examples, not a statement of legal requirements. Define and implement a reviewed retention schedule before launch.

## Security
Use HTTPS, secrets management, least-privilege database credentials, role-based access to admin tools, audit logs, backups, and a tested incident-response process. Do not place tokens or real customer records in GitHub.
