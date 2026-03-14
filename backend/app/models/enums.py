from enum import Enum


class OrderStatus(str, Enum):
    TEMP = "TEMP"
    CLOSE = "CLOSE"