from __future__ import annotations

import functools
import inspect
import io
import json
from functools import cmp_to_key
from typing import Any, Callable, TypeVar, cast
from uuid import UUID, uuid5

from .args import UUID_NAMESPACE, ChoiceFuncImplementation, MatchedRule, Rule, RuleVals
from .selector import SEL, OptStackFrame, Selector

F = TypeVar("F", bound=Callable[..., Any])


class TraceItem:
    def __init__(
        self,
        func: ChoiceFunction,
        impl: ChoiceFuncImplementation,
        rules: list[MatchedRule],
        stack_info: list[inspect.FrameInfo],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        choice_kwargs: dict[str, Any],
    ) -> None:
        self.func = func
        self.impl = impl
        self.rules = rules
        self.stack_info = stack_info
        self.args = args
        self.kwargs = kwargs
        self.choice_kwargs = choice_kwargs
        self.items: list[TraceItem] = []

    def print_item(self, sb: io.TextIOBase, indent: int = 0) -> None:
        prefix = " " * indent
        rule_str = " -> ".join(f"{r.rule.selector} [{r.rule.impl.func.__name__}]" for r in self.rules) or "No rules"
        sb.write(f"{prefix}{self.func.interface.func.__name__} [{self.impl.func.__name__}]")
        sb.write(f"{prefix}  Args: {self.args}, Kwargs: {self.kwargs}, Choice Kwargs: {self.choice_kwargs}")
        sb.write(f"{prefix}  Rules: {rule_str}")
        for sub_item in self.items:
            sub_item.print_item(sb, indent + 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "func": str(self.func.id),
            "impl": str(self.impl.id),
            "rules": self.rules,
            "stack_info": [f"{fi.function} at {fi.filename}:{fi.lineno}" for fi in self.stack_info],
            "args": [str(a) for a in self.args],
            "kwargs": {k: str(v) for k, v in self.kwargs.items()},
            "choice_kwargs": {k: str(v) for k, v in self.choice_kwargs.items()},
            "items": [item.to_dict() for item in self.items],
        }


class Tracing:
    def __init__(self) -> None:
        self.items: list[TraceItem] = []
        self.stack: list[TraceItem] = []

    def begin(self, item: TraceItem) -> None:
        self.stack.append(item)

    def end(self) -> None:
        if not self.stack:
            raise MismatchedTrace()
        elif len(self.stack) == 1:
            self.items.append(self.stack.pop())
        else:
            ended = self.stack.pop()
            self.stack[-1].items.append(ended)


class Trace:
    def __init__(self, tracing: Tracing) -> None:
        self.items = tracing.items

    def __str__(self) -> str:
        sb = io.StringIO()
        for item in self.items:
            item.print_item(sb, 0)

        return sb.getvalue()

    def save(self, filename: str) -> None:
        with open(filename, "w") as f:
            json.dump(self, f, cls=ChoiceJSONEncoder, indent=2)


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
        self.id = uuid5(UUID_NAMESPACE, f"{interface.func.__module__}.{interface.func.__name__}")
        self.interface: ChoiceFuncImplementation = interface
        self.funcs: dict[UUID, ChoiceFuncImplementation] = {}
        self.rules: list[Rule] = []

    def _add_func(self, f: Callable[..., Any], func: ChoiceFuncImplementation) -> None:
        self.funcs[func.id] = func

    def _add_rule(self, selector: SEL, impl: ChoiceFuncImplementation, vals: RuleVals) -> None:
        self.rules.append(Rule(Selector(selector, str(impl)), impl, vals))

    def _sorted_selectors(self, stack_info: OptStackFrame = None) -> list[MatchedRule]:
        if not self.rules:
            return []
        if stack_info is None:
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
        stack_info = inspect.stack()
        rules = self._sorted_selectors(stack_info)
        impl = rules[-1].rule.impl if rules else self.interface

        choice_kwargs = impl.choice_kwargs(rules, args, kwargs)
        trace_status.call_begin(TraceItem(self, impl, rules, stack_info, args, kwargs, choice_kwargs))
        res = impl.func(*args, **choice_kwargs)
        trace_status.call_end()
        return res


registry: list[ChoiceFunction] = []


def rule(selector: SEL, impl: ChoiceFunction | ChoiceFuncImplementation, **kwargs: Any) -> None:
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
            registry.append(reg)

            # Return wrapper
            return cast(F, functools.wraps(func)(reg))
        else:
            # Choice implementation

            # Add to registry
            implements._add_func(func, func_args)
            return cast(F, functools.wraps(func)(func_args))

    return decorator_args


class ChoiceJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, TraceItem):
            return obj.to_dict()
        elif isinstance(obj, Trace):
            return {"items": [item.to_dict() for item in obj.items], "registry": {str(f.id): f for f in registry}}
        elif isinstance(obj, ChoiceFunction):
            return {
                "id": str(obj.id),
                "interface": obj.interface,
                "funcs": {str(k): v for k, v in obj.funcs.items()},
                "rules": obj.rules,
            }
        elif isinstance(obj, ChoiceFuncImplementation):
            return {
                "id": str(obj.id),
                "func": getattr(obj.func, "__name__", str(obj)),
                "defaults": {k: str(v) for k, v in obj.defaults.items()},
            }
        elif isinstance(obj, Rule):
            return {
                "selector": str(obj.selector),
                "impl": str(obj.impl.id),
                "vals": obj.vals.__name__,
            }
        elif isinstance(obj, MatchedRule):
            return {
                "rule": obj.rule,
                "captures": {k: str(v) for k, v in obj.captures.items()},
                "vals": {k: str(v) for k, v in obj.vals.items()},
            }
        try:
            return super().default(obj)
        except Exception:
            return type(obj).__name__
