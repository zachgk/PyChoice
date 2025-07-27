import functools
from typing import Any, Callable, TypeVar, cast

from .selector import SEL, selector_matches

F = TypeVar("F", bound=Callable[..., Any])


class ChoiceFunction:
    def __init__(self, interface: Callable[..., Any]) -> None:
        self.interface: Callable[..., Any] = interface
        self.funcs: dict[str, Callable[..., Any]] = {}
        self.rule_selectors: list[SEL] = []
        self.rule_impls: list[Callable[..., Any]] = []

    def _add_func(self, func: Callable[..., Any]) -> None:
        self.funcs[func.__name__] = func

    def _add_rule(self, selector: SEL, impl: Callable[..., Any]) -> None:
        self.rule_selectors.append(selector)
        self.rule_impls.append(impl)

    def __call__(self, *args: list[Any], **kwargs: dict[str, Any]) -> Any:
        for matches, rule_impl in zip(selector_matches(self.rule_selectors), self.rule_impls):
            if matches:
                return rule_impl(*args, **kwargs)

        # No matching rule
        return self.interface(*args, **kwargs)


func_registry: dict[str, ChoiceFunction] = {}


def func_rule(selector: SEL, impl: Callable[..., Any]) -> None:
    choice_fun = cast(ChoiceFunction, selector[-1])
    choice_fun._add_rule(selector[:-1], impl)


def func_impl(interface: ChoiceFunction) -> Callable[[F], F]:
    """Allows providing choice arguments.

    Extended description of function.

    Args:
        bar: Description of input argument.

    Returns:
        Description of return value
    """

    def decorator_args(func: F) -> F:
        # Add to registry
        interface._add_func(func)

        return func

    return decorator_args


def func_interface() -> Callable[[F], F]:
    """Allows providing choice arguments.

    Extended description of function.

    Args:
        bar: Description of input argument.

    Returns:
        Description of return value
    """

    def decorator_args(func: F) -> F:
        # Add to registry
        reg = ChoiceFunction(func)
        func_registry[func.__name__] = reg

        # Return wrapper
        return cast(F, functools.wraps(func)(reg))

    return decorator_args
