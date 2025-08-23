import functools
import inspect
from functools import cmp_to_key
from typing import Any, Callable, Optional, TypeVar, Union, cast

from .args import ChoiceFuncImplementation, MatchedRule, Rule, RuleVals
from .selector import SEL, Selector

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

    def _add_rule(self, selector: SEL, impl: ChoiceFuncImplementation, vals: RuleVals) -> None:
        self.rules.append(Rule(Selector(selector), impl, vals))

    def _sorted_selectors(self) -> list[MatchedRule]:
        if not self.rules:
            return []
        stack_info = inspect.stack()

        # Get indices and filter to only matching
        rules = []
        for r in self.rules:
            matches, capture = r.selector.matches(stack_info)
            if matches:
                rules.append(MatchedRule(r, capture))
        if not rules:
            return []

        def compare(a: MatchedRule, b: MatchedRule) -> int:
            return a.rule.selector.compare(b.rule.selector, stack_info)

        # Sort
        rules = sorted(rules, key=cmp_to_key(compare))

        # Prune non-matching implementations for arg overrides
        impl = rules[-1].rule.impl
        rules = [r for r in rules if r.rule.impl == impl]

        return rules

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        rules = self._sorted_selectors()
        impl = rules[-1].rule.impl if rules else self.interface

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
    choice_fun._add_rule(selector[:-1], impl, lambda _: kwargs)


def cap_rule(selector: SEL, impl: Union[ChoiceFunction, ChoiceFuncImplementation], vals: RuleVals) -> None:
    if isinstance(impl, ChoiceFunction):
        impl = impl.interface
    elif isinstance(impl, ChoiceFuncImplementation):
        pass
    else:
        raise NonRule()
    # Choose function implementation
    choice_fun = cast(ChoiceFunction, selector[-1])
    choice_fun._add_rule(selector[:-1], impl, vals)


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
