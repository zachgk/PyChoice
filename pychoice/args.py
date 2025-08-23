from __future__ import annotations

import inspect
from typing import Any, Callable, NamedTuple, TypeVar

from .selector import Selector

F = TypeVar("F", bound=Callable[..., Any])
type RuleVals = Callable[[dict[str, Any]], dict[str, Any]]


class Rule(NamedTuple):
    selector: Selector
    impl: ChoiceFuncImplementation
    vals: RuleVals


class MatchedRule:
    def __init__(self, rule: Rule, captures: dict[str, Any]) -> None:
        self.rule = rule
        self.captures = captures


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

    def choice_kwargs(self, rules: list[MatchedRule], args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        new_kwargs = {}
        for r in rules:
            new_kwargs.update(r.rule.vals(r.captures))
        new_kwargs.update(kwargs)
        return new_kwargs

    def __call__(self, rules: list[MatchedRule], args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        return self.func(*args, **self.choice_kwargs(rules, args, kwargs))
