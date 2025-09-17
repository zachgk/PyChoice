from __future__ import annotations

import inspect
from dataclasses import dataclass
from functools import cmp_to_key
from typing import Any, Callable, Optional, TypeVar
from uuid import UUID, uuid5

from .selector import OptStackFrame, SelectorItem, StackFrame

F = TypeVar("F", bound=Callable[..., Any])
type RuleVals = Callable[[list[dict[str, Any]]], Optional[tuple[ChoiceFuncImplementation | None, dict[str, Any]]]]

UUID_NAMESPACE = UUID("e7221d32-4940-4c49-b0e3-5f03446226ab")


@dataclass
class Rule:
    selector: Selector
    impl: ChoiceFuncImplementation | None
    vals: RuleVals
    doc: str | None = None

    def __str__(self) -> str:
        if self.impl is not None:
            return f"{self.selector} [{self.impl.func.__name__}]"
        else:
            return f"{self.selector}"


class MatchedRule:
    def __init__(self, rule: Rule | None, captures: list[dict[str, Any]]) -> None:
        if rule is None:
            rule = Rule(Selector([]), None, lambda c: None)
        self.rule = rule
        self.captures = captures

        vals = rule.vals(captures)
        if vals is not None:
            self.impl: ChoiceFuncImplementation | None = vals[0]
            self.vals: dict[str, Any] = vals[1]
        else:
            self.impl = None
            self.vals = {}


class MissingChoiceArg(Exception):
    def __init__(self, func: Callable[..., Any], choice_arg: str):
        msg = f"The function {func.__name__} is missing the expected choice kwarg {choice_arg}"
        super().__init__(msg)


class Selector:
    def __init__(self, items: list[SelectorItem], impl: str = "") -> None:
        self.items: list[SelectorItem] = items
        self.impl = impl

    def __str__(self) -> str:
        return f"{' '.join(str(i) for i in self.items)} => {self.impl}"

    def choice_function(self) -> Any:
        return self.items[-1].get_callable()

    # Returns the indices of selectors in sorted order with worst matching at 0 and best matching at -1.
    # Non-matching are not returned
    @staticmethod
    def sort(selectors: list[Selector]) -> list[int]:
        if not selectors:
            return []
        stack_info = inspect.stack()

        # Get indices and filter to only matching
        indices = [i for i, matches in enumerate(Selector.all_matches(selectors, stack_info)) if matches]

        def compare(a: int, b: int) -> int:
            return selectors[a].compare(selectors[b], stack_info)

        # Sort
        return sorted(indices, key=cmp_to_key(compare))

    @staticmethod
    def all_matches(selectors: list[Selector], stack_info: OptStackFrame = None) -> list[bool]:
        if not selectors:
            return []
        if stack_info is None:
            stack_info = inspect.stack()
        return [selector.matches(stack_info) is not None for selector in selectors]

    def matches(self, stack_info: OptStackFrame = None, rule: Rule | None = None) -> MatchedRule | None:
        if stack_info is None:
            stack_info = inspect.stack()
        if len(self.items) == 0:
            # Empty selector always matches
            return MatchedRule(rule, [])

        captures = []
        selector_index = len(self.items) - 1
        for frame_info in stack_info:
            if self.items[selector_index].matches(frame_info):
                captures.append(Selector._collect_captures(self.items[selector_index], frame_info))
                if selector_index == 0:
                    return MatchedRule(rule, list(reversed(captures)))
                else:
                    # More selector components
                    selector_index = selector_index - 1
        return None

    @staticmethod
    def _collect_captures(item: SelectorItem, frame_info: inspect.FrameInfo) -> dict[str, Any]:
        """Collect captures from each matching SelectorItem in the selector."""
        # Import Match here to avoid circular imports
        from .funcs import CallableSelectorItem, ChoiceFunction

        # Capture logic moved from Match.capture
        local_vars = frame_info.frame.f_locals

        # Check if we're in a ChoiceFunction.__call__ context
        if isinstance(item, CallableSelectorItem) and isinstance(item.func, ChoiceFunction):
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
                return dict(bound_args.arguments)
            except Exception:  # noqa: S110
                # Fall back to original behavior if binding fails
                pass

        # Original behavior for regular functions
        return dict(local_vars)

    # Expects selectors to be pre-filtered
    def compare(self, other: Selector, stack_info: StackFrame) -> int:
        a = self.items
        b = other.items
        a_selector_index = len(a) - 1
        b_selector_index = len(b) - 1
        for frame_info in stack_info:
            if a_selector_index < 0 and b_selector_index < 0:
                return 0
            elif a_selector_index < 0:
                return -1
            elif b_selector_index < 0:
                return 1
            a_matches = a[a_selector_index].matches(frame_info)
            b_matches = b[b_selector_index].matches(frame_info)
            if not a_matches and not b_matches:
                # Check next frame
                continue
            elif a_matches and b_matches:
                a_selector_index = a_selector_index - 1
                b_selector_index = b_selector_index - 1
            elif not a_matches and b_matches:
                # b has lower level match, takes precedence
                return -1
            elif a_matches and not b_matches:
                # a has lower level match, takes precedence
                return 1
        return 0

    # Compare selectors in general, not a particular situation
    # Returns -1 if a is a sub-selector of b.
    # Returns 1 if b is a sub-selector of a.
    # Returns 0 if no relation
    def generic_compare(self, other: Selector) -> int:
        a = self.items
        b = other.items
        a_selector_index = len(a) - 1
        b_selector_index = len(b) - 1
        while a_selector_index >= 0 and b_selector_index >= 0:
            if a[a_selector_index] == b[b_selector_index]:
                a_selector_index = a_selector_index - 1
                b_selector_index = b_selector_index - 1
            else:
                # Term mismatch. No sub_selector relation
                return 0

        if a_selector_index >= 0:
            return -1
        if b_selector_index >= 0:
            return 1

        # Selectors are equal
        return 0


class ChoiceFuncImplementation[O]:
    def __init__(self, choice_args: list[str], func: F):
        self.id = uuid5(UUID_NAMESPACE, f"{func.__module__}.{func.__name__}")
        self.func: Callable[..., O] = func

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
        self.defaults = defaults

    def choice_kwargs(self, rules: list[MatchedRule], args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        new_kwargs = {}
        for r in rules:
            new_kwargs.update(r.vals)
        new_kwargs.update(kwargs)
        return new_kwargs

    def __call__(self, rules: list[MatchedRule], args: tuple[Any, ...], kwargs: dict[str, Any]) -> O:
        return self.func(*args, **self.choice_kwargs(rules, args, kwargs))

    def __str__(self) -> str:
        return self.func.__name__
