from sqlalchemy.orm import Session

from app.models import Item
from app.services.local_seed_service import import_local_products_to_db


def seed_if_empty(db: Session) -> None:
    if db.query(Item).count() > 0:
        return

    import_local_products_to_db(db)