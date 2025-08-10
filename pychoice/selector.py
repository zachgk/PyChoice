import inspect
from functools import cmp_to_key
from typing import Any, Callable, Optional

SEL = list[Callable[..., Any]]
StackFrame = list[inspect.FrameInfo]
OptStackFrame = Optional[StackFrame]


# Returns the indices of selectors in sorted order with worst matching at 0 and best matching at -1.
# Non-matching are not returned
def sort_selectors(selectors: list[SEL]) -> list[int]:
    if not selectors:
        return []
    stack_info = inspect.stack()

    # Get indices and filter to only matching
    indices = [i for i, matches in enumerate(selectors_matches(selectors, stack_info)) if matches]

    def compare(a: int, b: int) -> int:
        return selector_compare(selectors[a], selectors[b], stack_info)

    # Sort
    return sorted(indices, key=cmp_to_key(compare))


def selectors_matches(selectors: list[SEL], stack_info: OptStackFrame = None) -> list[bool]:
    if not selectors:
        return []
    if stack_info is None:
        stack_info = inspect.stack()
    return [selector_matches(selector, stack_info) for selector in selectors]


def selector_matches(selector: SEL, stack_info: OptStackFrame = None) -> bool:
    if stack_info is None:
        stack_info = inspect.stack()
    selector_index = len(selector) - 1
    for frame_info in stack_info:
        if frame_info.frame.f_code == selector[selector_index].__code__:
            if selector_index == 0:
                # Finished matching selector
                return True
            else:
                # More selector components
                selector_index = selector_index - 1
    return False


# Expects selectors to be pre-filtered
def selector_compare(a: SEL, b: SEL, stack_info: StackFrame) -> int:
    a_selector_index = len(a) - 1
    b_selector_index = len(b) - 1
    for frame_info in stack_info:
        a_matches = frame_info.frame.f_code == a[a_selector_index].__code__
        b_matches = frame_info.frame.f_code == b[b_selector_index].__code__
        if not a_matches and not b_matches:
            # Check next frame
            continue
        elif a_matches and b_matches:
            a_selector_index = a_selector_index - 1
            b_selector_index = b_selector_index - 1
            if a_selector_index < 0 and b_selector_index < 0:
                return 0
            elif a_selector_index < 0:
                return -1
            elif b_selector_index < 0:
                return 1
        elif not a_matches and b_matches:
            # b has lower level match, takes precedence
            return -1
        elif a_matches and not b_matches:
            # a has lower level match, takes precedence
            return 1
    return 0
