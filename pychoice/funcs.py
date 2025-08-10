import functools
import inspect
from functools import cmp_to_key
from typing import Any, Callable, Optional, TypeVar, Union, cast

from .args import ChoiceFuncImplementation, Rule
from .selector import SEL, selector_compare, selector_matches

F = TypeVar("F", bound=Callable[..., Any])


class NonRule(Exception):
    def __init__(self) -> None:
        super().__init__("Expected a choice function for the rule impl")


class ChoiceFunction:
    def __init__(self, interface: ChoiceFuncImplementation) -> None:
        self.interface: ChoiceFuncImplementation = interface
        self.funcs: dict[str, ChoiceFuncImplementation] = {}
        self.rules: list[Rule] = []

    def _add_func(self, f: Callable[..., Any], func: ChoiceFuncImplementation) -> None:
        self.funcs[f.__name__] = func

    def _add_rule(self, selector: SEL, impl: ChoiceFuncImplementation, vals: dict[str, Any]) -> None:
        self.rules.append(Rule(selector, impl, vals))

    def _sorted_selectors(self) -> list[Rule]:
        if not self.rules:
            return []
        rules = self.rules
        stack_info = inspect.stack()

        # Get indices and filter to only matching
        rules = [r for r in rules if selector_matches(r.selector, stack_info)]
        if not rules:
            return []

        def compare(a: Rule, b: Rule) -> int:
            return selector_compare(a.selector, b.selector, stack_info)

        # Sort
        rules = sorted(rules, key=cmp_to_key(compare))

        # Prune non-matching implementations for arg overrides
        impl = rules[-1].impl
        rules = [r for r in rules if r.impl == impl]

        return rules

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        rules = self._sorted_selectors()
        impl = rules[-1].impl if rules else self.interface

        return impl(rules, args, kwargs)


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
    choice_fun._add_rule(selector[:-1], impl, kwargs)


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
