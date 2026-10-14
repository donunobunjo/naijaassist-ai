# Demo data dictionary

All rows are synthetic and must not be treated as real product offers, real market prices, or real stock.

- `products.csv`: 200 products (120 phone entries and 80 accessory entries); stable catalogue attributes.
- `product_prices.csv`: current demo prices in NGN. `status=approved` means approved within this fictional dataset only.
- `inventory.csv`: synthetic quantity and timestamp.
- Timestamps use ISO-8601 UTC (`+00:00`).
- Every SKU in price/inventory CSVs must match one in `products.csv`.
- CSVs are starter fixtures. Before publishing, make sure the README and app UI clearly label them as synthetic.
