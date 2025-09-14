from __future__ import annotations

import inspect
from contextvars import ContextVar
from types import TracebackType
from typing import Any, Callable, Optional, Union


class ChoiceContext:
    active = ContextVar("active", default=False)

    def __enter__(self) -> None:
        self.active.set(True)

    def __exit__(
        self, exc_type: BaseException | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> bool | None:
        self.active.set(False)
        return None


class SelectorItem:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    def get_callable(self) -> Callable[..., Any] | None:
        raise NotImplementedError

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        raise NotImplementedError


SEL_I_CLS = tuple[type, str]
SEL_I = Union[Callable[..., Any], SEL_I_CLS, ChoiceContext, SelectorItem]
SEL = list[Callable[..., Any]]
StackFrame = list[inspect.FrameInfo]
OptStackFrame = Optional[StackFrame]


class InvalidSelectorItem(TypeError):
    def __init__(self, item: SEL_I):
        msg = f"Invalid selector item type: {type(item)} for {item}"
        super().__init__(msg)


class NonFunction(TypeError):
    def __init__(self) -> None:
        super().__init__("Expected a choice function for the final term in a selector")


class ChoiceContextSelectorItem(SelectorItem):
    def __init__(self, context: type[ChoiceContext]):
        self.context = context

    def __str__(self) -> str:
        return f"ChoiceContext(active={self.context.active.get()})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ChoiceContextSelectorItem) and self.context == other.context

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        return self.context.active.get()


class FunctionSelectorItem(SelectorItem):
    def __init__(self, func: Callable[..., Any]):
        self.func = func

    def __str__(self) -> str:
        return self.func.__name__

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FunctionSelectorItem) and self.func == other.func

    def get_callable(self) -> Callable[..., Any] | None:
        return self.func

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        return self.func.__code__ == frame_info.frame.f_code


class CallableSelectorItem(SelectorItem):
    def __init__(self, func: Callable[..., Any]):
        self.func: Callable[..., Any] = func

    def __str__(self) -> str:
        return self.func.__name__

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CallableSelectorItem) and self.func == other.func

    def get_callable(self) -> Callable[..., Any] | None:
        return self.func

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        if not hasattr(self.func.__call__, "__code__"):  # type: ignore[operator]
            return False
        if self.func.__call__.__code__ != frame_info.frame.f_code:  # type: ignore[operator]
            return False
        return not (hasattr(self.func, "__class__") and self.func != frame_info.frame.f_locals.get("self", None))


class ClassSelectorItem(SelectorItem):
    def __init__(self, cls: type, func_name: str):
        self.cls = cls
        self.qual_name = f"{cls.__name__}.{func_name}"
        self.func_name = func_name

    def __str__(self) -> str:
        return self.qual_name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ClassSelectorItem) and self.cls == other.cls and self.func_name == other.func_name

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        if frame_info.frame.f_code.co_name == self.func_name:
            qualname = frame_info.frame.f_code.co_qualname
            parts = qualname.split(".")
            if len(parts) > 1:
                class_name = parts[0]
                module = inspect.getmodule(frame_info.frame)
                cls = getattr(module, class_name, None)
                if not isinstance(cls, type):
                    return False
                return cls == self.cls or issubclass(cls, self.cls)
        return False
