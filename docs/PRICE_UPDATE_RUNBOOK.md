# Price Update Runbook

## CSV format
`data/product_prices.csv` requires:
- `sku`: existing unique SKU.
- `price_ngn`: non-negative decimal amount.
- `updated_at`: ISO-8601 timestamp with timezone.
- `status`: `approved`, `pending`, or `retired`.

Example:

```csv
sku,price_ngn,updated_at,status
NMH-PHN-0001,280000.00,2026-10-14T00:00:00+00:00,approved
```

## Update procedure
1. Obtain an authorized, verified price sheet.
2. Review the SKU, amount, status, timestamp, and approval authority.
3. Edit a copy of the price CSV; do not edit inventory accidentally.
4. Run the importer against the database. The importer validates all three input files and imports within a transaction.
5. Review the import summary and audit history.
6. Test price lookup and stale-price behavior.
7. Commit only non-sensitive synthetic fixtures to GitHub; never commit a real retailer's confidential price list.

## Important limitations in the starter
- The CSV importer is an implementation starting point, not a complete approval/admin workflow.
- The first imported price establishes the initial current price; subsequent changed prices create history rows.
- `changed_by` is currently the fixed label `csv-import`. Before production, require authenticated operator identity and an approval/audit workflow.
- Do not allow an untrusted user to upload a price CSV directly.
