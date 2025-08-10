from __future__ import annotations

import inspect
from functools import cmp_to_key
from typing import Any, Callable, Optional, Union

SEL_I_CLS = tuple[type, str]
SEL_I = Union[Callable[..., Any]]
SEL = list[Callable[..., Any]]
StackFrame = list[inspect.FrameInfo]
OptStackFrame = Optional[StackFrame]


class SelectorItem:
    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func

    def __str__(self) -> str:
        return self.func.__name__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SelectorItem):
            return False
        return self.func == other.func

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        """
        Check if this selector item matches the current stack frame.
        """
        return self.func.__code__ == frame_info.frame.f_code


class Selector:
    def __init__(self, items: SEL) -> None:
        self.items: list[SelectorItem] = [SelectorItem(i) for i in items]

    def __str__(self) -> str:
        return f"Selector({', '.join(str(i) for i in self.items)})"

    # Returns the indices of selectors in sorted order with worst matching at 0 and best matching at -1.
    # Non-matching are not returned
    @staticmethod
    def sort(selectors: list[Selector]) -> list[int]:
        if not selectors:
            return []
        stack_info = inspect.stack()

        # Get indices and filter to only matching
        indices = [i for i, matches in enumerate(Selector.all_matches(selectors, stack_info)) if matches]

        def compare(a: int, b: int) -> int:
            return selectors[a].compare(selectors[b], stack_info)

        # Sort
        return sorted(indices, key=cmp_to_key(compare))

    @staticmethod
    def all_matches(selectors: list[Selector], stack_info: OptStackFrame = None) -> list[bool]:
        if not selectors:
            return []
        if stack_info is None:
            stack_info = inspect.stack()
        return [selector.matches(stack_info) for selector in selectors]

    def matches(self, stack_info: OptStackFrame = None) -> bool:
        if stack_info is None:
            stack_info = inspect.stack()
        selector_index = len(self.items) - 1
        for frame_info in stack_info:
            if self.items[selector_index].matches(frame_info):
                if selector_index == 0:
                    # Finished matching selector
                    return True
                else:
                    # More selector components
                    selector_index = selector_index - 1
        return False

    # Expects selectors to be pre-filtered
    def compare(self, other: Selector, stack_info: StackFrame) -> int:
        a = self.items
        b = other.items
        a_selector_index = len(a) - 1
        b_selector_index = len(b) - 1
        for frame_info in stack_info:
            a_matches = a[a_selector_index].matches(frame_info)
            b_matches = b[b_selector_index].matches(frame_info)
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

    # Compare selectors in general, not a particular situation
    # Returns -1 if a is a sub-selector of b.
    # Returns 1 if b is a sub-selector of a.
    # Returns 0 if no relation
    def generic_compare(self, other: Selector) -> int:
        a = self.items
        b = other.items
        a_selector_index = len(a) - 1
        b_selector_index = len(b) - 1
        while a_selector_index >= 0 and b_selector_index >= 0:
            if a[a_selector_index] == b[b_selector_index]:
                a_selector_index = a_selector_index - 1
                b_selector_index = b_selector_index - 1
            else:
                # Term mismatch. No sub_selector relation
                return 0

        if a_selector_index >= 0:
            return -1
        if b_selector_index >= 0:
            return 1

        # Selectors are equal
        return 0
