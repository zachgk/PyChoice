from __future__ import annotations

import inspect
from functools import cmp_to_key
from typing import Any, Callable, NamedTuple, Optional, Union

SEL_I_CLS = tuple[type, str]
SEL_I = Union[Callable[..., Any], SEL_I_CLS]
SEL = list[Callable[..., Any]]
StackFrame = list[inspect.FrameInfo]
OptStackFrame = Optional[StackFrame]


class InvalidSelectorItem(TypeError):
    def __init__(self, item: SEL_I):
        msg = f"Invalid selector item type: {type(item)} for {item}"
        super().__init__(msg)


class Match(NamedTuple):
    func: Callable[..., Any]
    args: list[str]


class SelectorItem:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    def matches(self, frame_info: inspect.FrameInfo) -> tuple[bool, dict[str, Any]]:
        raise NotImplementedError

    def capture(self, frame_info: inspect.FrameInfo) -> dict[str, Any]:
        return {}


class FunctionSelectorItem(SelectorItem):
    def __init__(self, func: Callable[..., Any]):
        self.func = func

    def __str__(self) -> str:
        return self.func.__name__

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FunctionSelectorItem) and self.func == other.func

    def matches(self, frame_info: inspect.FrameInfo) -> tuple[bool, dict[str, Any]]:
        return self.func.__code__ == frame_info.frame.f_code, {}


class ClassSelectorItem(SelectorItem):
    def __init__(self, cls: type, func_name: str):
        self.cls = cls
        self.qual_name = f"{cls.__name__}.{func_name}"
        self.func_name = func_name

    def __str__(self) -> str:
        return self.qual_name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ClassSelectorItem) and self.cls == other.cls and self.func_name == other.func_name

    def matches(self, frame_info: inspect.FrameInfo) -> tuple[bool, dict[str, Any]]:
        if frame_info.frame.f_code.co_name == self.func_name:
            qualname = frame_info.frame.f_code.co_qualname
            parts = qualname.split(".")
            if len(parts) > 1:
                class_name = parts[0]
                module = inspect.getmodule(frame_info.frame)
                cls = getattr(module, class_name, None)
                if not isinstance(cls, type):
                    return False, {}
                return cls == self.cls or issubclass(cls, self.cls), {}
        return False, {}


class MatchSelectorItem(SelectorItem):
    def __init__(self, func: Callable[..., Any], match_args: list[str]):
        self.func = func
        self.match_args = match_args

    def __str__(self) -> str:
        return f"{self.func.__name__}({', '.join(self.match_args)})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MatchSelectorItem) and self.func == other.func and self.match_args == other.match_args

    def matches(self, frame_info: inspect.FrameInfo) -> tuple[bool, dict[str, Any]]:
        if self.func.__code__ != frame_info.frame.f_code:
            return False, {}
        return True, self.capture(frame_info)

    def capture(self, frame_info: inspect.FrameInfo) -> dict[str, Any]:
        local_vars = frame_info.frame.f_locals
        return {arg: local_vars[arg] for arg in self.match_args if arg in local_vars}


class Selector:
    def __init__(self, items: SEL) -> None:
        self.items: list[SelectorItem] = []
        for i in items:
            if isinstance(i, tuple) and len(i) == 2 and isinstance(i[0], type) and isinstance(i[1], str):
                self.items.append(ClassSelectorItem(i[0], i[1]))
            elif isinstance(i, Match):
                self.items.append(MatchSelectorItem(i.func, i.args))
            elif callable(i):
                self.items.append(FunctionSelectorItem(i))
            else:
                raise InvalidSelectorItem(i)

    def __str__(self) -> str:
        return " ".join(str(i) for i in self.items)

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
        return [selector.matches(stack_info)[0] for selector in selectors]

    def matches(self, stack_info: OptStackFrame = None) -> tuple[bool, dict[str, Any]]:
        if stack_info is None:
            stack_info = inspect.stack()
        if len(self.items) == 0:
            return True, {}
        captures = {}
        selector_index = len(self.items) - 1
        for frame_info in stack_info:
            frame_matches, frame_captures = self.items[selector_index].matches(frame_info)
            if frame_matches:
                captures.update(frame_captures)
                if selector_index == 0:
                    # Finished matching selector
                    return True, captures
                else:
                    # More selector components
                    selector_index = selector_index - 1
        return False, {}

    # Expects selectors to be pre-filtered
    def compare(self, other: Selector, stack_info: StackFrame) -> int:
        a = self.items
        b = other.items
        a_selector_index = len(a) - 1
        b_selector_index = len(b) - 1
        for frame_info in stack_info:
            if a_selector_index < 0 and b_selector_index < 0:
                return 0
            elif a_selector_index < 0:
                return -1
            elif b_selector_index < 0:
                return 1
            a_matches = a[a_selector_index].matches(frame_info)
            b_matches = b[b_selector_index].matches(frame_info)
            if not a_matches and not b_matches:
                # Check next frame
                continue
            elif a_matches and b_matches:
                a_selector_index = a_selector_index - 1
                b_selector_index = b_selector_index - 1
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
