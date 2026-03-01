from sqlalchemy.orm import Session
from app.repositories.items_repo import count_items, create_item


SEED_ITEMS = [
    ("Milk", 6.9, 12),
    ("Bread", 8.5, 7),
    ("Eggs", 14.9, 0),
    ("Coffee", 29.9, 5),
    ("Rice 1kg", 12.9, 18),
    ("Tomatoes", 9.9, 22),
    ("Olive oil", 39.9, 3),
    ("Pasta", 7.9, 15),
    ("Cheese", 18.9, 4),
    ("Chocolate", 11.9, 0),
]


def seed_if_empty(db: Session) -> None:
    if count_items(db) > 0:
        return

    for name, price, stock in SEED_ITEMS:
        create_item(db, name=name, price_usd=price, stock_qty=stock)