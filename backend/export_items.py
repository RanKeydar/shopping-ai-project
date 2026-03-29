from __future__ import annotations

import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models import Item


OUTPUT_FILE = Path(__file__).resolve().parent / "app" / "data" / "products_seed.json"


def main() -> None:
    db = SessionLocal()
    try:
        items = db.query(Item).all()

        data = []
        for item in items:
            data.append(
                {
                    "name": item.name,
                    "price_usd": float(item.price_usd),
                    "stock_qty": int(item.stock_qty),
                    "category": item.category,
                    "description": item.description,
                }
            )

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Exported {len(data)} items to {OUTPUT_FILE}")
    finally:
        db.close()


if __name__ == "__main__":
    main()