from __future__ import annotations

import functools
import inspect
import io
import json
from functools import cmp_to_key
from typing import Any, Callable, TypeVar, cast
from uuid import UUID, uuid5

from .args import UUID_NAMESPACE, ChoiceFuncImplementation, MatchedRule, Rule, RuleVals
from .selector import (
    SEL,
    SEL_I,
    CallableSelectorItem,
    ChoiceContext,
    ChoiceContextSelectorItem,
    ClassSelectorItem,
    FunctionSelectorItem,
    InvalidSelectorItem,
    OptStackFrame,
    Selector,
    SelectorItem,
)

F = TypeVar("F", bound=Callable[..., Any])


class Match(SelectorItem):
    def __init__(self, func: SEL_I, match_args: list[str]):
        self.item = new_selector_item(func)
        self.match_args = match_args

    def __str__(self) -> str:
        return str(self.item)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Match) and self.item == other.item and self.match_args == other.match_args

    def get_callable(self) -> Callable[..., Any] | None:
        return self.item.get_callable()

    def matches(self, frame_info: inspect.FrameInfo) -> tuple[bool, dict[str, Any]]:
        if not self.item.matches(frame_info)[0]:
            return False, {}
        return True, self.capture(frame_info)

    def capture(self, frame_info: inspect.FrameInfo) -> dict[str, Any]:
        local_vars = frame_info.frame.f_locals

        # Check if we're in a ChoiceFunction.__call__ context
        if isinstance(self.item, CallableSelectorItem) and isinstance(self.item.func, ChoiceFunction):
            choice_func = local_vars["self"]
            args = local_vars.get("args", ())
            kwargs = local_vars.get("kwargs", {})

            # Get the signature of the actual function
            sig = inspect.signature(choice_func.interface.func)

            # Bind the arguments to get the actual parameter values
            try:
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # Return only the requested match_args
                return {arg: bound_args.arguments[arg] for arg in self.match_args if arg in bound_args.arguments}
            except Exception:  # noqa: S110
                # Fall back to original behavior if binding fails
                pass

        # Original behavior for regular functions
        return {arg: local_vars[arg] for arg in self.match_args if arg in local_vars}


def new_selector_item(item: SEL_I) -> SelectorItem:
    if isinstance(item, type) and issubclass(item, ChoiceContext):
        return ChoiceContextSelectorItem(item)
    elif isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], type) and isinstance(item[1], str):
        return ClassSelectorItem(item[0], item[1])
    elif isinstance(item, SelectorItem):
        return item
    elif callable(item) and hasattr(item, "__code__"):
        return FunctionSelectorItem(item)
    elif callable(item):
        return CallableSelectorItem(item)
    else:
        raise InvalidSelectorItem(item)


def new_selector(items: SEL, impl: str = "") -> Selector:
    sel_items = [new_selector_item(i) for i in items]
    return Selector(sel_items, impl)


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
        rule_str = " -> ".join(str(r) for r in self.rules) or "No rules"
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


class ChoiceFunction[O]:
    def __init__(self, interface: ChoiceFuncImplementation[O]) -> None:
        self.id = uuid5(UUID_NAMESPACE, f"{interface.func.__module__}.{interface.func.__name__}")
        self.interface: ChoiceFuncImplementation[O] = interface
        self.funcs: dict[UUID, ChoiceFuncImplementation[O]] = {}
        self.rules: list[Rule] = []

    def __str__(self) -> str:
        return f"ChoiceFunction({self.interface.func.__name__})"

    def _add_func(self, f: Callable[..., Any], func: ChoiceFuncImplementation[O]) -> None:
        self.funcs[func.id] = func

    def _add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)

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

    def __call__(self, *args: Any, **kwargs: Any) -> O:
        stack_info = inspect.stack()
        rules = self._sorted_selectors(stack_info)

        impl = self.interface
        for rule in reversed(rules):
            if rule.impl is not None:
                impl = rule.impl  # Override with best matched rule if one is applicable
                break

        if isinstance(impl, ChoiceFuncImplementation):
            pass
        elif isinstance(impl, ChoiceFunction):
            impl = impl.interface
        else:
            raise NonRule()

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
    sel = new_selector(selector, str(impl))
    choice_fun = sel.choice_function()
    if isinstance(choice_fun, ChoiceFunction):
        choice_fun = cast(ChoiceFunction, choice_fun)
    else:
        raise TypeError()
    choice_fun._add_rule(Rule(sel, impl, lambda _: (impl, kwargs)))


def def_rule(selector: SEL) -> Any:
    def decorator_args(func: RuleVals) -> RuleVals:
        # Choose function implementation
        sel = new_selector(selector)
        choice_fun = sel.choice_function()
        if isinstance(choice_fun, ChoiceFunction):
            choice_fun = cast(ChoiceFunction, choice_fun)
        else:
            raise TypeError()
        choice_fun._add_rule(Rule(sel, None, func, inspect.getdoc(func)))
        return func

    return decorator_args


def func[O](args: list[str] | None = None) -> Callable[[Callable[..., O]], ChoiceFunction[O]]:
    if args is None:
        args = []

    def decorator_args(func: F) -> ChoiceFunction[O]:
        func_args = ChoiceFuncImplementation[O](args, func)
        # Choice interface

        # Add to registry
        reg = ChoiceFunction[O](func_args)
        registry.append(reg)

        # Return wrapper
        return cast(ChoiceFunction[O], functools.wraps(func)(reg))

    return decorator_args


def impl[O](
    implements: ChoiceFunction[O], args: list[str] | None = None
) -> Callable[[Callable[..., O]], ChoiceFuncImplementation[O]]:
    if args is None:
        args = []

    def decorator_args(func: F) -> ChoiceFuncImplementation[O]:
        func_args = ChoiceFuncImplementation[O](args, func)
        # Choice implementation

        # Add to registry
        implements._add_func(func, func_args)
        return cast(ChoiceFuncImplementation[O], functools.wraps(func)(func_args))

    return decorator_args


def wrap[O](
    f: Callable[..., O], implements: ChoiceFunction[O], args: list[str] | None = None
) -> ChoiceFuncImplementation[O]:
    return impl(implements, args=args)(f)


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
                "module": getattr(obj.func, "__module__", ""),
                "defaults": {k: str(v) for k, v in obj.defaults.items()},
                "doc": inspect.getdoc(obj.func),
            }
        elif isinstance(obj, Rule):
            return {
                "selector": str(obj.selector),
                "impl": str(obj.impl.id if obj.impl is not None else None),
                "doc": obj.doc,
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
