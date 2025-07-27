import inspect
from typing import Any, Callable

SEL = list[Callable[..., Any]]


def selector_matches(selectors: list[SEL]) -> list[bool]:
    if not selectors:
        return []
    res = []
    stack_info = inspect.stack()
    for selector in selectors:
        selector_matches = False
        for frame_info in stack_info:
            # TODO Support multi-element selectors
            if frame_info.frame.f_code == selector[0].__code__:
                selector_matches = True
                break

        res.append(selector_matches)

    return res
