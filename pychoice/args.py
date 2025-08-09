import functools
import inspect
from typing import Any, Callable, TypeVar, cast

from .selector import SEL, sort_selectors

F = TypeVar("F", bound=Callable[..., Any])


class ChoiceArg:
    def __init__(self, func: Callable[..., Any], defaults: dict[str, Any]):
        self.func = func
        self.defaults = defaults
        self.rule_selectors: list[SEL] = []
        self.rule_vals: list[dict[str, Any]] = []

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


registry: dict[str, ChoiceArg] = {}


class MissingChoiceArg(Exception):
    def __init__(self, func: Callable[..., Any], choice_arg: str):
        msg = f"The function {func.__name__} is missing the expected choice kwarg {choice_arg}"
        super().__init__(msg)


def arg_rule(selector: SEL, **kwargs: dict[str, Any]) -> None:
    choice_arg = cast(ChoiceArg, selector[-1])
    choice_arg._add_rule(selector[:-1], kwargs)


def args(*choice_args: str) -> Callable[[F], F]:
    """Allows providing choice arguments.

    This function decorator lets you turn a function into one supporting choice arguments.

    Args:
        choice_args: The args from the decorated function to support as choice arguments

    Returns:
        The function wrapped with choice argument support
    """

    def decorator_args(func: F) -> F:
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

        # Add to registry
        reg = ChoiceArg(func, defaults)
        registry[func.__name__] = reg

        # Return wrapper
        return cast(F, functools.wraps(func)(reg))

    return decorator_args
