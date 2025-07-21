import functools
import inspect
from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


class ArgRegistry:
    def __init__(self, defaults: dict[str, Any]):
        self.defaults = defaults
        self.rules: list[tuple[str, dict[str, Any]]] = []

    def add_rule(self, selector: str, vals: dict[str, Any]) -> None:
        self.rules.append((selector, vals))


registry: dict[str, ArgRegistry] = {}


class MissingChoiceArg(Exception):
    def __init__(self, func: Callable[..., Any], choice_arg: str):
        msg = f"The function {func.__name__} is missing the expected choice kwarg {choice_arg}"
        super().__init__(msg)


def arg_rule(func: str, selector: str, **kwargs: dict[str, Any]) -> None:
    registry[func].add_rule(selector, kwargs)


def args(*choice_args: str) -> Callable[[F], F]:
    """Allows providing choice arguments.

    Extended description of function.

    Args:
        bar: Description of input argument.

    Returns:
        Description of return value
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
        registry[func.__name__] = ArgRegistry(defaults)

        # Return wrapper
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator_args
