from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])


@router.get("")
def list_items():
    # Phase 1: mock data
    return [
        {"id": 1, "name": "Milk", "price": 6.9},
        {"id": 2, "name": "Bread", "price": 8.5},
    ]
