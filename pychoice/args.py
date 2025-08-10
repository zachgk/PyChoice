from __future__ import annotations

import inspect
from typing import Any, Callable, NamedTuple, TypeVar

from .selector import SEL

F = TypeVar("F", bound=Callable[..., Any])


class Rule(NamedTuple):
    selector: SEL
    impl: ChoiceFuncImplementation
    vals: dict[str, Any]


class MissingChoiceArg(Exception):
    def __init__(self, func: Callable[..., Any], choice_arg: str):
        msg = f"The function {func.__name__} is missing the expected choice kwarg {choice_arg}"
        super().__init__(msg)


class ChoiceFuncImplementation:
    def __init__(self, choice_args: list[str], func: F):
        self.func = func

        # Collect args
        sig = inspect.signature(func)
        defaults = {}
        for param in sig.parameters.values():
            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                defaults[param.name] = param.default

        # Validate args
        for choice_arg in choice_args:
            if choice_arg not in defaults:
                raise MissingChoiceArg(func, choice_arg)
        self.defaults = defaults

    def __call__(self, rules: list[Rule], args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        new_kwargs = {}
        for r in rules:
            new_kwargs.update(r.vals)
        new_kwargs.update(kwargs)

        # No matching rule
        return self.func(*args, **new_kwargs)
