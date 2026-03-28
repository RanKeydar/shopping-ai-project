from __future__ import annotations

from frontend.features.orders.types import OrderDict, OrdersPageData


def find_open_order(orders_list: list[OrderDict]) -> OrderDict | None:
    for order in orders_list:
        if order.get("status") == "TEMP":
            return order
    return None


def get_order_by_id(
    orders_list: list[OrderDict],
    order_id: int | None,
) -> OrderDict | None:
    if order_id is None:
        return None

    for order in orders_list:
        if order.get("id") == order_id:
            return order
    return None


def resolve_selected_order_id(
    orders_list: list[OrderDict],
    current_selected_order_id: int | None,
) -> int | None:
    if not orders_list:
        return None

    selected_order = get_order_by_id(orders_list, current_selected_order_id)
    if selected_order is not None:
        return selected_order.get("id")

    open_order = find_open_order(orders_list)
    if open_order is not None:
        return open_order.get("id")

    return orders_list[0].get("id")


def build_orders_page_data(
    orders_list: list[OrderDict],
    current_selected_order_id: int | None,
) -> OrdersPageData:
    open_order = find_open_order(orders_list)
    selected_order_id = resolve_selected_order_id(
        orders_list=orders_list,
        current_selected_order_id=current_selected_order_id,
    )
    selected_order = get_order_by_id(orders_list, selected_order_id)

    return OrdersPageData(
        orders_list=orders_list,
        open_order=open_order,
        selected_order_id=selected_order_id,
        selected_order=selected_order,
    )