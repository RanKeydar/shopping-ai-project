from __future__ import annotations

from dataclasses import dataclass
from typing import Any


OrderDict = dict[str, Any]


@dataclass
class OrdersPageData:
    orders_list: list[OrderDict]
    open_order: OrderDict | None
    selected_order_id: int | None
    selected_order: OrderDict | None