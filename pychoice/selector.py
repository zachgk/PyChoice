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
        selector_index = len(selector) - 1
        for frame_info in stack_info:
            if frame_info.frame.f_code == selector[selector_index].__code__:
                if selector_index == 0:
                    # Finished matching selector
                    selector_matches = True
                    break
                else:
                    # More selector components
                    selector_index = selector_index - 1

        res.append(selector_matches)

    return res
