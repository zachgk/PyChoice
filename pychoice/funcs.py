from __future__ import annotations

import functools
import inspect
from functools import cmp_to_key
from typing import Any, Callable, TypeVar, cast

from .args import ChoiceFuncImplementation, MatchedRule, Rule, RuleVals
from .selector import SEL, Selector

F = TypeVar("F", bound=Callable[..., Any])


class TraceItem:
    def __init__(self, func: ChoiceFunction) -> None:
        self.func = func
        self.items: list[TraceItem] = []


class Tracing:
    def __init__(self) -> None:
        self.count = 0
        self.items: list[TraceItem] = []
        self.stack: list[TraceItem] = []

    def begin(self, item: TraceItem) -> None:
        self.count += 1
        self.stack.append(item)

    def end(self) -> None:
        if not self.stack:
            raise MismatchedTrace()
        elif len(self.stack) == 1:
            self.items.append(self.stack.pop())
        else:
            self.items[-1].items.append(self.stack.pop())


class Trace:
    def __init__(self, tracing: Tracing) -> None:
        self.count = tracing.count
        self.items = tracing.items
        self.registry = registry


class TraceStatus:
    def __init__(self) -> None:
        self.trace: Tracing | None = None

    def call_begin(self, item: TraceItem) -> None:
        if self.trace is not None:
            self.trace.begin(item)

    def call_end(self) -> None:
        if self.trace is not None:
            self.trace.end()

    def start(self) -> None:
        self.trace = Tracing()

    def stop(self) -> Trace:
        trace = self.trace if self.trace is not None else Tracing()
        self.trace = None
        return Trace(trace)


trace_status = TraceStatus()


class NonRule(Exception):
    def __init__(self) -> None:
        super().__init__("Expected a choice function for the rule impl")


class MismatchedTrace(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Mismatched choice Trace end call")


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

        trace_status.call_begin(TraceItem(self))
        res = impl(rules, args, kwargs)
        trace_status.call_end()
        return res


registry: dict[str, ChoiceFunction] = {}


def rule(selector: SEL, impl: ChoiceFunction | ChoiceFuncImplementation, **kwargs: dict[str, Any]) -> None:
    if isinstance(impl, ChoiceFunction):
        impl = impl.interface
    elif isinstance(impl, ChoiceFuncImplementation):
        pass
    else:
        raise NonRule()
    # Choose function implementation
    choice_fun = cast(ChoiceFunction, selector[-1])
    choice_fun._add_rule(selector[:-1], impl, lambda _: kwargs)


def cap_rule(selector: SEL, impl: ChoiceFunction | ChoiceFuncImplementation, vals: RuleVals) -> None:
    if isinstance(impl, ChoiceFunction):
        impl = impl.interface
    elif isinstance(impl, ChoiceFuncImplementation):
        pass
    else:
        raise NonRule()
    # Choose function implementation
    choice_fun = cast(ChoiceFunction, selector[-1])
    choice_fun._add_rule(selector[:-1], impl, vals)


def def_rule(selector: SEL, impl: ChoiceFunction | ChoiceFuncImplementation) -> Any:
    if isinstance(impl, ChoiceFunction):
        impl = impl.interface
    elif isinstance(impl, ChoiceFuncImplementation):
        pass
    else:
        raise NonRule()

    def decorator_args(func: RuleVals) -> RuleVals:
        # Choose function implementation
        choice_fun = cast(ChoiceFunction, selector[-1])
        choice_fun._add_rule(selector[:-1], impl, func)
        return func

    return decorator_args


def func(implements: ChoiceFunction | None = None, args: list[str] | None = None) -> Callable[[F], F]:
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
