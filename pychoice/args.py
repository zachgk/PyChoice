"""Core argument handling and rule management for PyChoice.

This module contains the fundamental classes for defining and managing choice rules,
selectors, and implementations. It handles the logic for matching selectors against
call stacks and applying the appropriate implementations.
"""

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
    """Represents a choice rule that defines when and how to customize function behavior.

    A Rule combines a Selector (which defines when the rule applies) with an
    implementation and values (which define how to customize the behavior).

    Attributes:
        selector: The Selector that determines when this rule matches
        impl: The ChoiceFuncImplementation to use, or None for parameter-only rules
        vals: Function that converts captures to implementation and values
        doc: Optional documentation string for the rule

    Example:
        ```python
        # Rule that changes greeting in my_app context
        rule = Rule(
            selector=Selector([my_app, greet]),
            impl=greet_impl,
            vals=lambda c: (greet_impl, {"greeting": "Hi"})
        )
        ```
    """

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
    """Represents a rule that has been matched against a call stack.

    When a Selector matches a call stack, it creates a MatchedRule containing
    the original rule, captured variables, and resolved implementation details.

    Attributes:
        rule: The original Rule that was matched
        captures: List of variable dictionaries captured from matching stack frames
        impl: The resolved ChoiceFuncImplementation to use
        vals: The resolved parameter values to apply

    Example:
        ```python
        # When a rule matches, it becomes a MatchedRule
        matched = MatchedRule(rule, captured_vars)
        # matched.impl contains the implementation to use
        # matched.vals contains the parameter overrides
        ```
    """

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
    """Exception raised when a choice function is missing expected arguments.

    This occurs when a @choice.func decorator specifies choice arguments that
    don't exist as parameters in the decorated function.

    Example:
        ```python
        @choice.func(args=["nonexistent"])  # This arg doesn't exist
        def greet(name: str):  # Missing "nonexistent" parameter
            return f"Hello {name}"
        # Raises MissingChoiceArg
        ```
    """

    def __init__(self, func: Callable[..., Any], choice_arg: str):
        msg = f"The function {func.__name__} is missing the expected choice kwarg {choice_arg}"
        super().__init__(msg)


class Selector:
    """Defines a pattern for matching against function call stacks.

    A Selector contains a list of SelectorItems that must match in order
    from the deepest to shallowest call stack frames. It's used to determine
    when choice rules should be applied.

    Attributes:
        items: List of SelectorItems that define the matching pattern
        impl: Implementation identifier string for display purposes

    Example:
        ```python
        # Match when greet() is called from my_app()
        selector = Selector([my_app, greet])
        ```
    """

    def __init__(self, items: list[SelectorItem], impl: str = "") -> None:
        self.items: list[SelectorItem] = items
        self.impl = impl

    def __str__(self) -> str:
        return f"{' '.join(str(i) for i in self.items)} => {self.impl}"

    def choice_function(self) -> Any:
        """Get the choice function that this selector targets.

        Returns:
            The callable from the last SelectorItem, typically a choice function
        """
        return self.items[-1].get_callable()

    @staticmethod
    def sort(selectors: list[Selector]) -> list[int]:
        """Sort selectors by specificity, returning indices.

        Returns indices of selectors sorted from least specific (0) to most
        specific (-1). Non-matching selectors are excluded.

        Args:
            selectors: List of selectors to sort

        Returns:
            List of indices in specificity order (most specific last)
        """
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
        """Check which selectors match the current call stack.

        Args:
            selectors: List of selectors to check
            stack_info: Optional stack frames, uses current stack if None

        Returns:
            Boolean list indicating which selectors match
        """
        if not selectors:
            return []
        if stack_info is None:
            stack_info = inspect.stack()
        return [selector.matches(stack_info) is not None for selector in selectors]

    def matches(self, stack_info: OptStackFrame = None, rule: Rule | None = None) -> MatchedRule | None:
        """Check if this selector matches the given call stack.

        Args:
            stack_info: Stack frames to match against, uses current if None
            rule: Associated rule for creating MatchedRule

        Returns:
            MatchedRule if selector matches, None otherwise
        """
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
        """Collect variable captures from a matching stack frame.

        Args:
            item: The SelectorItem that matched
            frame_info: The stack frame that was matched

        Returns:
            Dictionary of captured local variables
        """
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

    def compare(self, other: Selector, stack_info: StackFrame) -> int:
        """Compare selector specificity for a given call stack.

        Args:
            other: Other selector to compare against
            stack_info: Call stack to compare within

        Returns:
            -1 if self is less specific, 1 if more specific, 0 if equal
        """
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

    def generic_compare(self, other: Selector) -> int:
        """Compare selectors generically without specific call stack context.

        Args:
            other: Other selector to compare against

        Returns:
            -1 if self is sub-selector of other, 1 if other is sub-selector of self, 0 if no relation
        """
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
    """Implementation wrapper for choice functions.

    This class wraps a regular function to make it usable as a choice function
    implementation, handling parameter validation, rule application, and invocation.

    Attributes:
        id: Unique identifier for this implementation
        func: The wrapped function
        defaults: Default parameter values from the function signature

    Example:
        ```python
        # Create an implementation for a greeting function
        impl = ChoiceFuncImplementation(["greeting"], greet_func)
        result = impl(matched_rules, ("John",), {})
        ```
    """

    def __init__(self, choice_args: list[str], func: F):
        """Initialize a choice function implementation.

        Args:
            choice_args: List of parameter names that can be customized by rules
            func: The function to wrap as a choice implementation

        Raises:
            MissingChoiceArg: If any choice_arg is not a parameter of func
        """
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
        """Merge rule values with provided kwargs.

        Args:
            rules: List of matched rules to apply
            args: Positional arguments (unused but kept for consistency)
            kwargs: Keyword arguments from the call

        Returns:
            Merged dictionary of keyword arguments with rule values applied
        """
        new_kwargs = {}
        for r in rules:
            new_kwargs.update(r.vals)
        new_kwargs.update(kwargs)
        return new_kwargs

    def __call__(self, rules: list[MatchedRule], args: tuple[Any, ...], kwargs: dict[str, Any]) -> O:
        """Execute the implementation with rule-modified parameters.

        Args:
            rules: List of matched rules to apply
            args: Positional arguments to pass to the function
            kwargs: Keyword arguments to pass to the function

        Returns:
            Result of calling the wrapped function with modified parameters
        """
        return self.func(*args, **self.choice_kwargs(rules, args, kwargs))

    def __str__(self) -> str:
        return self.func.__name__
