from typing import Union


def format_boolean(value: Union[bool, None]) -> str:
    if value is None:
        return "unknown"
    return "+" if value else "-"


def add_scheme_from_auth_host(url: str, auth_host: str) -> str:
    """
    Add scheme to url if it doesn't have one.
    - auth_host with https, use https
    - auth_host with http, use http
    - already has scheme? as is
    """
    if "://" in url:
        return url

    if "://" in auth_host:
        return auth_host.split("://")[0] + "://" + url

    return "http://" + url
