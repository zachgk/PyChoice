import functools
from typing import Any, Callable, Optional, TypeVar, Union, cast

from .args import ChoiceFuncImplementation
from .selector import SEL, sort_selectors

F = TypeVar("F", bound=Callable[..., Any])


class NonRule(Exception):
    def __init__(self) -> None:
        super().__init__("Expected a choice function for the rule impl")


class ChoiceFunction:
    def __init__(self, interface: ChoiceFuncImplementation) -> None:
        self.interface: ChoiceFuncImplementation = interface
        self.funcs: dict[str, ChoiceFuncImplementation] = {}
        self.rule_selectors: list[SEL] = []
        self.rule_impls: list[ChoiceFuncImplementation] = []

    def _add_func(self, f: Callable[..., Any], func: ChoiceFuncImplementation) -> None:
        self.funcs[f.__name__] = func

    def _add_rule(self, selector: SEL, impl: ChoiceFuncImplementation) -> None:
        self.rule_selectors.append(selector)
        self.rule_impls.append(impl)

    def __call__(self, *args: list[Any], **kwargs: dict[str, Any]) -> Any:
        # TODO Use a more performant max_selector rather than sort_selectors
        selector_indices = sort_selectors(self.rule_selectors)
        if selector_indices:
            return self.rule_impls[selector_indices[-1]](*args, **kwargs)

        # No matching rule
        return self.interface(*args, **kwargs)


registry: dict[str, ChoiceFunction] = {}


def rule(selector: SEL, impl: Union[ChoiceFunction, ChoiceFuncImplementation], **kwargs: dict[str, Any]) -> None:
    if isinstance(impl, ChoiceFunction):
        impl = impl.interface
    elif isinstance(impl, ChoiceFuncImplementation):
        pass
    else:
        raise NonRule()
    # Choose function implementation
    choice_fun = cast(ChoiceFunction, selector[-1])
    choice_fun._add_rule(selector[:-1], impl)

    # Choose function arguments
    impl._add_rule(selector[:-1], kwargs)


def func(implements: Optional[ChoiceFunction] = None, args: Optional[list[str]] = None) -> Callable[[F], F]:
    if args is None:
        args = []

    def decorator_args(func: F) -> F:
        func_args = ChoiceFuncImplementation(args, func)
        if implements is None:
            # Choice interface

            # Add to registry
            reg = ChoiceFunction(func_args)
            registry[func.__name__] = reg

            # Return wrapper
            return cast(F, functools.wraps(func)(reg))
        else:
            # Choice implementation

            # Add to registry
            implements._add_func(func, func_args)
            return cast(F, functools.wraps(func)(func_args))

    return decorator_args
