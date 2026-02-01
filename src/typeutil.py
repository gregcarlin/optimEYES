from typing import TypeVar

T = TypeVar("T")


def none_throws(x: T | None) -> T:
    assert x is not None
    return x
