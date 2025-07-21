import functools
from typing import Any, Callable, Optional, TypeVar, cast

from .selector import selector_matches

F = TypeVar("F", bound=Callable[..., Any])


class FuncRegistry:
    def __init__(self) -> None:
        self.interface: Optional[Callable[..., Any]] = None
        self.funcs: dict[str, Callable[..., Any]] = {}
        self.rule_selectors: list[str] = []
        self.rule_vals: list[str] = []

    def set_interface(self, interface: Callable[..., Any]) -> None:
        self.interface = interface

    def add_func(self, func: Callable[..., Any]) -> None:
        self.funcs[func.__name__] = func

    def add_rule(self, selector: str, vals: str) -> None:
        self.rule_selectors.append(selector)
        self.rule_vals.append(vals)


func_registry: dict[str, FuncRegistry] = {}


def func_rule(interface: str, selector: str, impl: str) -> None:
    func_registry[interface].add_rule(selector, impl)


def func_impl(name: str) -> Callable[[F], F]:
    """Allows providing choice arguments.

    Extended description of function.

    Args:
        bar: Description of input argument.

    Returns:
        Description of return value
    """

    def decorator_args(func: F) -> F:
        # Add to registry
        if name not in func_registry:
            func_registry[name] = FuncRegistry()
        func_registry[name].add_func(func)

        return func

    return decorator_args


def func_interface(name: str) -> Callable[[F], F]:
    """Allows providing choice arguments.

    Extended description of function.

    Args:
        bar: Description of input argument.

    Returns:
        Description of return value
    """

    def decorator_args(func: F) -> F:
        # Add to registry
        if name not in func_registry:
            func_registry[name] = FuncRegistry()
        reg = func_registry[name]
        reg.set_interface(func)

        # Return wrapper
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for matches, rule_val in zip(selector_matches(reg.rule_selectors), reg.rule_vals):
                if matches:
                    return reg.funcs[rule_val](*args, **kwargs)

            # No matching rule
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator_args
