# Order Management — Demo Version

**No real order or payment integration is active in this starter repository.**

1. Order lookup must use a controlled tool and a verified customer/order relationship.
2. Do not reveal another customer's order details.
3. Order status must come from the trusted order system, not from memory or a language-model guess.
4. Before purchase confirmation, re-check approved price, inventory, delivery eligibility, and any active promotion.
5. If the price has changed since a prior quote, explain the difference and ask the customer to confirm the new price before proceeding.
6. Never state an order was placed, paid, dispatched, delivered, cancelled, or refunded unless the trusted system confirms the action.
7. The assistant must not perform arbitrary database writes from natural-language instructions.
