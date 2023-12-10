from typing import Union


def format_boolean(value: Union[bool, None]) -> str:
    if value is None:
        return "unknown"
    return "+" if value else "-"
