#!/usr/bin/env python3
"""Validate and transactionally import product, price and inventory CSV files."""
import argparse
import csv
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg


load_dotenv()

REQUIRED_PRODUCTS = {
    "sku", "brand", "model", "category", "condition", "description",
    "ram_gb", "storage_gb", "display_inches", "battery_mah", "camera_mp",
    "os", "connectivity", "warranty_months", "active",
}
REQUIRED_PRICES = {"sku", "price_ngn", "updated_at", "status"}
REQUIRED_INVENTORY = {"sku", "quantity", "updated_at"}


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing = required - headers
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: file has no data rows")
    return rows


def parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp must include a timezone: {value}")
    return parsed.astimezone(timezone.utc)


def validate_rows(products, prices, inventory):
    product_skus = [r["sku"].strip() for r in products]
    if len(product_skus) != len(set(product_skus)):
        raise ValueError("products.csv contains duplicate SKUs")
    product_set = set(product_skus)

    for row in products:
        if row["condition"] not in {"New", "Refurbished", "Used"}:
            raise ValueError(f"Invalid condition for {row['sku']}")
        for field in ("ram_gb", "storage_gb", "warranty_months"):
            if row[field].strip() and int(row[field]) < 0:
                raise ValueError(f"Negative {field} for {row['sku']}")
        if row["active"].lower() not in {"true", "false", "1", "0"}:
            raise ValueError(f"Invalid active value for {row['sku']}")

    for rows, label in ((prices, "prices"), (inventory, "inventory")):
        skus = [r["sku"].strip() for r in rows]
        if len(skus) != len(set(skus)):
            raise ValueError(f"{label}.csv contains duplicate SKUs")
        unknown = set(skus) - product_set
        if unknown:
            raise ValueError(f"{label}.csv contains unknown SKUs: {', '.join(sorted(unknown)[:10])}")

    for row in prices:
        try:
            price = Decimal(row["price_ngn"])
        except InvalidOperation as exc:
            raise ValueError(f"Invalid price for {row['sku']}") from exc
        if not price.is_finite() or price < 0:
            raise ValueError(f"Price must be finite and non-negative for {row['sku']}")
        if row["status"] not in {"approved", "pending", "retired"}:
            raise ValueError(f"Invalid price status for {row['sku']}")
        parse_datetime(row["updated_at"])

    for row in inventory:
        if int(row["quantity"]) < 0:
            raise ValueError(f"Negative inventory quantity for {row['sku']}")
        parse_datetime(row["updated_at"])


def import_files(database_url: str, products_path: Path, prices_path: Path, inventory_path: Path):
    products = read_csv(products_path, REQUIRED_PRODUCTS)
    prices = read_csv(prices_path, REQUIRED_PRICES)
    inventory = read_csv(inventory_path, REQUIRED_INVENTORY)
    validate_rows(products, prices, inventory)

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                for row in products:
                    cur.execute(
                        """
                        INSERT INTO products
                        (sku, brand, model, category, condition, description, ram_gb, storage_gb,
                         display_inches, battery_mah, camera_mp, os, connectivity, warranty_months, active)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (sku) DO UPDATE SET
                          brand=EXCLUDED.brand, model=EXCLUDED.model, category=EXCLUDED.category,
                          condition=EXCLUDED.condition, description=EXCLUDED.description,
                          ram_gb=EXCLUDED.ram_gb, storage_gb=EXCLUDED.storage_gb,
                          display_inches=EXCLUDED.display_inches, battery_mah=EXCLUDED.battery_mah,
                          camera_mp=EXCLUDED.camera_mp, os=EXCLUDED.os,
                          connectivity=EXCLUDED.connectivity, warranty_months=EXCLUDED.warranty_months,
                          active=EXCLUDED.active, updated_at=now()
                        """,
                        (
                            row["sku"], row["brand"], row["model"], row["category"], row["condition"],
                            row["description"], int(row["ram_gb"]) if row["ram_gb"] else None,
                            int(row["storage_gb"]) if row["storage_gb"] else None,
                            float(row["display_inches"]) if row["display_inches"] else None,
                            int(row["battery_mah"]) if row["battery_mah"] else None,
                            float(row["camera_mp"]) if row["camera_mp"] else None,
                            row["os"], row["connectivity"],
                            int(row["warranty_months"]) if row["warranty_months"] else None,
                            row["active"].lower() in {"true", "1"},
                        ),
                    )

                for row in prices:
                    new_price = Decimal(row["price_ngn"])
                    updated_at = parse_datetime(row["updated_at"])
                    cur.execute("SELECT price_ngn FROM product_prices WHERE sku=%s FOR UPDATE", (row["sku"],))
                    previous = cur.fetchone()
                    if previous is not None and Decimal(previous[0]) != new_price:
                        cur.execute(
                            """INSERT INTO product_price_history
                            (sku, old_price_ngn, new_price_ngn, changed_at, changed_by, change_source)
                            VALUES (%s,%s,%s,%s,%s,%s)""",
                            (row["sku"], previous[0], new_price, updated_at, "csv-import", "csv"),
                        )
                    cur.execute(
                        """INSERT INTO product_prices (sku, price_ngn, updated_at, status)
                        VALUES (%s,%s,%s,%s)
                        ON CONFLICT (sku) DO UPDATE SET
                          price_ngn=EXCLUDED.price_ngn, updated_at=EXCLUDED.updated_at,
                          status=EXCLUDED.status""",
                        (row["sku"], new_price, updated_at, row["status"]),
                    )

                for row in inventory:
                    cur.execute(
                        """INSERT INTO inventory (sku, quantity, updated_at)
                        VALUES (%s,%s,%s)
                        ON CONFLICT (sku) DO UPDATE SET
                          quantity=EXCLUDED.quantity, updated_at=EXCLUDED.updated_at""",
                        (row["sku"], int(row["quantity"]), parse_datetime(row["updated_at"])),
                    )
    print(f"Imported {len(products)} products, {len(prices)} prices, {len(inventory)} inventory records.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--products", type=Path, default=Path("data/products.csv"))
    parser.add_argument("--prices", type=Path, default=Path("data/product_prices.csv"))
    parser.add_argument("--inventory", type=Path, default=Path("data/inventory.csv"))
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    args = parser.parse_args()
    if not args.database_url:
        parser.error("Set DATABASE_URL or pass --database-url")
    import_files(args.database_url, args.products, args.prices, args.inventory)


if __name__ == "__main__":
    main()
