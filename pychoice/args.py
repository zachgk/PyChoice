import inspect
from typing import Any, Callable, TypeVar

from .selector import SEL, sort_selectors

F = TypeVar("F", bound=Callable[..., Any])


class MissingChoiceArg(Exception):
    def __init__(self, func: Callable[..., Any], choice_arg: str):
        msg = f"The function {func.__name__} is missing the expected choice kwarg {choice_arg}"
        super().__init__(msg)


class ChoiceFuncImplementation:
    def __init__(self, choice_args: list[str], func: F):
        self.func = func
        self.rule_selectors: list[SEL] = []
        self.rule_vals: list[dict[str, Any]] = []

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

    def _add_rule(self, selector: SEL, vals: dict[str, Any]) -> None:
        self.rule_selectors.append(selector)
        self.rule_vals.append(vals)

    def __call__(self, *args: list[Any], **kwargs: dict[str, Any]) -> Any:
        new_kwargs = {}
        for i in sort_selectors(self.rule_selectors):
            new_kwargs.update(self.rule_vals[i])
        new_kwargs.update(kwargs)

        # No matching rule
        return self.func(*args, **new_kwargs)
