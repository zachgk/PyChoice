from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar
from uuid import UUID, uuid5

from .selector import Selector

F = TypeVar("F", bound=Callable[..., Any])
type RuleVals = Callable[[dict[str, Any]], Optional[tuple[ChoiceFuncImplementation, dict[str, Any]]]]

UUID_NAMESPACE = UUID("e7221d32-4940-4c49-b0e3-5f03446226ab")


@dataclass
class Rule:
    selector: Selector
    impl: ChoiceFuncImplementation | None
    vals: RuleVals
    doc: str | None = None

    def __str__(self) -> str:
        if self.impl is not None:
            return f"{self.selector} [{self.impl.func.__name__}]"
        else:
            return f"{self.selector}"


class MatchedRule:
    def __init__(self, rule: Rule, captures: dict[str, Any]) -> None:
        self.rule = rule
        self.captures = captures

        vals = rule.vals(captures)
        if vals is not None:
            self.impl: ChoiceFuncImplementation | None = vals[0]
            self.vals: dict[str, Any] = vals[1]
        else:
            self.impl = None
            self.vals = {}


class MissingChoiceArg(Exception):
    def __init__(self, func: Callable[..., Any], choice_arg: str):
        msg = f"The function {func.__name__} is missing the expected choice kwarg {choice_arg}"
        super().__init__(msg)


class ChoiceFuncImplementation[O]:
    def __init__(self, choice_args: list[str], func: F):
        self.id = uuid5(UUID_NAMESPACE, f"{func.__module__}.{func.__name__}")
        self.func: Callable[..., O] = func

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

    def choice_kwargs(self, rules: list[MatchedRule], args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        new_kwargs = {}
        for r in rules:
            new_kwargs.update(r.vals)
        new_kwargs.update(kwargs)
        return new_kwargs

    def __call__(self, rules: list[MatchedRule], args: tuple[Any, ...], kwargs: dict[str, Any]) -> O:
        return self.func(*args, **self.choice_kwargs(rules, args, kwargs))

    def __str__(self) -> str:
        return self.func.__name__
