"""Core functionality for PyChoice - choice functions, decorators, and tracing.

This module contains the primary implementation of choice functions, including
decorators for creating choice functions and implementations, tracing capabilities,
and the core ChoiceFunction class that handles rule matching and execution.
"""

from __future__ import annotations

import functools
import inspect
import io
import json
from functools import cmp_to_key
from typing import Any, Callable, TypeVar, cast
from uuid import UUID, uuid5

from .args import UUID_NAMESPACE, ChoiceFuncImplementation, MatchedRule, Rule, RuleVals, Selector
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
    SelectorItem,
)

F = TypeVar("F", bound=Callable[..., Any])


class Match(SelectorItem):
    """Advanced selector item that matches function calls with specific argument values.
    
    Match extends basic function matching to also check argument values, allowing
    for more precise rule targeting based on function parameters.
    
    Attributes:
        item: The underlying SelectorItem to match
        match_kwargs: Keyword arguments that must match for this selector to apply
        
    Example:
        ```python
        # Match greet() calls where greeting="Hi"
        match_item = Match(greet, greeting="Hi")
        selector = Selector([my_app, match_item])
        ```
    """
    def __init__(self, func: SEL_I, **kwargs: Any):
        self.item = new_selector_item(func)
        self.match_kwargs = kwargs

    def __str__(self) -> str:
        return str(self.item)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Match) and self.item == other.item and self.match_kwargs == other.match_kwargs

    def get_callable(self) -> Callable[..., Any] | None:
        """Get the underlying callable from the wrapped selector item."""
        return self.item.get_callable()

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        """Check if this Match selector matches a stack frame.
        
        First checks if the underlying item matches, then verifies that
        all specified keyword arguments match the actual call arguments.
        
        Args:
            frame_info: Stack frame to check for matching
            
        Returns:
            True if both function and arguments match, False otherwise
        """
        # First check if the underlying item matches
        if not self.item.matches(frame_info):
            return False

        # If no kwargs to match, then it's a match
        if not self.match_kwargs:
            return True

        # Capture the arguments and compare against expected kwargs
        captured = self.capture(frame_info)

        # Check if all expected kwargs match the captured values
        for key, expected_value in self.match_kwargs.items():
            if key not in captured or captured[key] != expected_value:
                return False

        return True

    def capture(self, frame_info: inspect.FrameInfo) -> dict[str, Any]:
        """Capture local variables from the matching stack frame.
        
        Args:
            frame_info: Stack frame to capture variables from
            
        Returns:
            Dictionary of captured local variables
        """
        return Selector._collect_captures(self.item, frame_info)


def new_selector_item(item: SEL_I) -> SelectorItem:
    """Create a SelectorItem from various input types.
    
    This factory function converts different types of selector inputs into
    appropriate SelectorItem instances for use in Selectors.
    
    Args:
        item: Input item to convert (function, class, tuple, etc.)
        
    Returns:
        Appropriate SelectorItem subclass instance
        
    Raises:
        InvalidSelectorItem: If the input type cannot be converted
        
    Example:
        ```python
        # Convert function to selector item
        func_item = new_selector_item(my_function)
        
        # Convert class method to selector item  
        method_item = new_selector_item((MyClass, "method_name"))
        ```
    """
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
    """Create a Selector from a list of selector inputs.
    
    Convenience function that converts a list of various selector inputs
    into SelectorItems and creates a Selector.
    
    Args:
        items: List of selector inputs (functions, classes, etc.)
        impl: Optional implementation identifier string
        
    Returns:
        Selector instance with converted SelectorItems
        
    Example:
        ```python
        # Create selector for my_app -> greet call chain
        selector = new_selector([my_app, greet])
        ```
    """
    sel_items = [new_selector_item(i) for i in items]
    return Selector(sel_items, impl)


class TraceItem:
    """Represents a single choice function call in a trace.
    
    TraceItems capture the complete context of a choice function invocation,
    including which implementation was used, what rules applied, and the
    arguments involved. They form a hierarchical structure to represent
    nested choice function calls.
    
    Attributes:
        func: The ChoiceFunction that was called
        impl: The ChoiceFuncImplementation that was executed
        rules: List of MatchedRules that applied to this call
        stack_info: Call stack information at time of invocation
        args: Positional arguments passed to the function
        kwargs: Keyword arguments passed to the function
        choice_kwargs: Final keyword arguments after rule application
        items: List of nested TraceItems for sub-calls
    """
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
        """Initialize a TraceItem with complete call context.
        
        Args:
            func: The ChoiceFunction that was invoked
            impl: The implementation that was selected and executed
            rules: List of rules that matched and applied
            stack_info: Call stack frames at time of invocation
            args: Positional arguments to the function
            kwargs: Original keyword arguments 
            choice_kwargs: Final keyword arguments after rule processing
        """
        self.func = func
        self.impl = impl
        self.rules = rules
        self.stack_info = stack_info
        self.args = args
        self.kwargs = kwargs
        self.choice_kwargs = choice_kwargs
        self.items: list[TraceItem] = []

    def print_item(self, sb: io.TextIOBase, indent: int = 0) -> None:
        """Print formatted representation of this trace item.
        
        Args:
            sb: Text buffer to write output to
            indent: Indentation level for nested display
        """
        prefix = " " * indent
        rule_str = " -> ".join(str(r) for r in self.rules) or "No rules"
        sb.write(f"{prefix}{self.func.interface.func.__name__} [{self.impl.func.__name__}]")
        sb.write(f"{prefix}  Args: {self.args}, Kwargs: {self.kwargs}, Choice Kwargs: {self.choice_kwargs}")
        sb.write(f"{prefix}  Rules: {rule_str}")
        for sub_item in self.items:
            sub_item.print_item(sb, indent + 2)

    def to_dict(self) -> dict[str, Any]:
        """Convert trace item to dictionary representation.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
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
    """Manages the collection of trace items during tracing.
    
    Tracing maintains the active stack of TraceItems as choice functions
    are called, building a hierarchical structure of invocations.
    
    Attributes:
        items: Completed top-level trace items
        stack: Current stack of active trace items
    """
    def __init__(self) -> None:
        self.items: list[TraceItem] = []
        self.stack: list[TraceItem] = []

    def begin(self, item: TraceItem) -> None:
        """Begin tracing a new choice function call.
        
        Args:
            item: TraceItem for the function call being started
        """
        self.stack.append(item)

    def end(self) -> None:
        """End tracing the most recent choice function call.
        
        Raises:
            MismatchedTrace: If there are no active calls to end
        """
        if not self.stack:
            raise MismatchedTrace()
        elif len(self.stack) == 1:
            self.items.append(self.stack.pop())
        else:
            ended = self.stack.pop()
            self.stack[-1].items.append(ended)


class Trace:
    """Contains the complete trace of choice function calls.
    
    A Trace represents the final result of tracing, containing all
    choice function invocations that occurred during the traced period.
    
    Attributes:
        items: List of top-level TraceItems representing the call hierarchy
        
    Example:
        ```python
        trace_start()
        my_application()  # Contains choice function calls
        trace = trace_stop()
        print(trace)  # Shows all choice decisions made
        trace.save("choices.json")  # Save for analysis
        ```
    """
    def __init__(self, tracing: Tracing) -> None:
        self.items = tracing.items

    def __str__(self) -> str:
        sb = io.StringIO()
        for item in self.items:
            item.print_item(sb, 0)

        return sb.getvalue()

    def save(self, filename: str) -> None:
        """Save trace to JSON file for analysis.
        
        Args:
            filename: Path to save the JSON trace file
            
        Example:
            ```python
            trace.save("debug_choices.json")
            ```
        """
        with open(filename, "w") as f:
            json.dump(self, f, cls=ChoiceJSONEncoder, indent=2)


class TraceStatus:
    """Global tracing state manager.
    
    TraceStatus maintains the global state of tracing, allowing
    trace collection to be started and stopped. It's used internally
    by the trace_start() and trace_stop() functions.
    
    Attributes:
        trace: Current active Tracing instance, or None if not tracing
    """
    def __init__(self) -> None:
        self.trace: Tracing | None = None

    def call_begin(self, item: TraceItem) -> None:
        """Record the beginning of a choice function call.
        
        Args:
            item: TraceItem representing the call being started
        """
        if self.trace is not None:
            self.trace.begin(item)

    def call_end(self) -> None:
        """Record the end of a choice function call."""
        if self.trace is not None:
            self.trace.end()

    def start(self) -> None:
        """Start a new tracing session."""
        self.trace = Tracing()

    def stop(self) -> Trace:
        """Stop tracing and return collected trace.
        
        Returns:
            Trace object containing all collected choice function calls
        """
        trace = self.trace if self.trace is not None else Tracing()
        self.trace = None
        return Trace(trace)


trace_status = TraceStatus()


class NonRule(Exception):
    """Exception raised when an invalid rule implementation is provided.
    
    This occurs when trying to create a rule with something that is not
    a ChoiceFunction or ChoiceFuncImplementation.
    """
    def __init__(self) -> None:
        super().__init__("Expected a choice function for the rule impl")


class MismatchedTrace(RuntimeError):
    """Exception raised when trace begin/end calls are mismatched.
    
    This occurs when trace_end() is called without a corresponding
    trace_begin(), indicating a bug in the tracing logic.
    """
    def __init__(self) -> None:
        super().__init__("Mismatched choice Trace end call")


class ChoiceFunction[O]:
    """The core choice function that manages rules and dispatches to implementations.
    
    ChoiceFunction is created by the @func decorator and serves as the central
    orchestrator for choice-based function calls. It maintains a registry of
    rules and alternative implementations, selecting the most appropriate one
    based on the current call stack.
    
    Attributes:
        id: Unique identifier for this choice function
        interface: The default ChoiceFuncImplementation
        funcs: Dictionary of alternative implementations by UUID
        rules: List of rules that apply to this choice function
        
    Example:
        ```python
        @choice.func(args=["greeting"])
        def greet(name: str, greeting="Hello"):
            return f"{greeting} {name}"
        # greet is now a ChoiceFunction instance
        ```
    """
    def __init__(self, interface: ChoiceFuncImplementation[O]) -> None:
        """Initialize a ChoiceFunction with a default implementation.
        
        Args:
            interface: The default ChoiceFuncImplementation to use
        """
        self.id = uuid5(UUID_NAMESPACE, f"{interface.func.__module__}.{interface.func.__name__}")
        self.interface: ChoiceFuncImplementation[O] = interface
        self.funcs: dict[UUID, ChoiceFuncImplementation[O]] = {}
        self.rules: list[Rule] = []

    def __str__(self) -> str:
        return f"ChoiceFunction({self.interface.func.__name__})"

    def _add_func(self, f: Callable[..., Any], func: ChoiceFuncImplementation[O]) -> None:
        """Add an alternative implementation to this choice function.
        
        Args:
            f: The original function (unused but kept for compatibility)
            func: The ChoiceFuncImplementation to add
        """
        self.funcs[func.id] = func

    def _add_rule(self, rule: Rule) -> None:
        """Add a rule to this choice function.
        
        Args:
            rule: The Rule to add to the rule list
        """
        self.rules.append(rule)

    def _sorted_selectors(self, stack_info: OptStackFrame = None) -> list[MatchedRule]:
        """Get matching rules sorted by specificity.
        
        Args:
            stack_info: Optional stack frames, uses current stack if None
            
        Returns:
            List of MatchedRules sorted from least to most specific
        """
        if not self.rules:
            return []
        if stack_info is None:
            stack_info = inspect.stack()

        # Get indices and filter to only matching
        rules = []
        for r in self.rules:
            matched_rule = r.selector.matches(stack_info, r)
            if matched_rule is not None:
                rules.append(matched_rule)
        if not rules:
            return []

        def compare(a: MatchedRule, b: MatchedRule) -> int:
            return a.rule.selector.compare(b.rule.selector, stack_info)

        # Sort
        rules = sorted(rules, key=cmp_to_key(compare))

        return rules

    def __call__(self, *args: Any, **kwargs: Any) -> O:
        stack_info = inspect.stack()
        rules = self._sorted_selectors(stack_info)

        impl = self.interface
        for rule in reversed(rules):
            if rule.impl is not None:
                impl = rule.impl  # Override with best matched rule if one is applicable
                break

        # Prune non-matching implementations for arg overrides
        rules = [r for r in rules if r.rule.impl == impl or r.rule.impl is None]

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
"""Global registry of all ChoiceFunctions created with @func decorator."""


def rule(selector: SEL, impl: ChoiceFunction | ChoiceFuncImplementation | None, **kwargs: Any) -> None:
    """Create a choice rule that customizes function behavior in specific contexts.
    
    Rules define when and how to customize choice functions. They specify a selector
    (which determines when the rule applies) and either an alternative implementation
    or parameter overrides.
    
    Args:
        selector: List defining the call stack pattern to match
        impl: ChoiceFunction, ChoiceFuncImplementation, or None for parameter-only rules
        **kwargs: Parameter values to apply when this rule matches
        
    Example:
        ```python
        # Parameter-only rule
        choice.rule([my_app, greet], greet, greeting="Hi")
        
        # Implementation-switching rule
        choice.rule([formal_context, greet], formal_greet_impl)
        ```
    """
    if impl is None:
        # Allow None implementation for args-only rules
        processed_impl = None
    elif isinstance(impl, ChoiceFunction):
        processed_impl = impl.interface
    elif isinstance(impl, ChoiceFuncImplementation):
        processed_impl = impl
    else:
        raise NonRule()
    # Choose function implementation
    sel = new_selector(selector, str(processed_impl) if processed_impl is not None else "")
    choice_fun = sel.choice_function()
    if isinstance(choice_fun, ChoiceFunction):
        choice_fun = cast(ChoiceFunction, choice_fun)
    else:
        raise TypeError()
    choice_fun._add_rule(Rule(sel, processed_impl, lambda _: (processed_impl, kwargs)))


def def_rule(selector: SEL) -> Any:
    """Decorator for creating dynamic rules with custom logic.
    
    Unlike simple rules created with rule(), def_rule allows you to create
    rules with custom logic that can dynamically determine parameter values
    based on captured variables from the call stack.
    
    Args:
        selector: List defining the call stack pattern to match
        
    Returns:
        Decorator function for the rule implementation
        
    Example:
        ```python
        @choice.def_rule([debug_mode, log])
        def debug_log_rule(captures):
            # Custom logic based on captured variables
            return None, {"level": "DEBUG", "verbose": True}
        ```
    """
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
    """Decorator to create a choice function from a regular function.
    
    This is the primary decorator for creating choice functions. It converts
    a regular function into a ChoiceFunction that can be customized through rules.
    
    Args:
        args: List of parameter names that can be customized by rules
        
    Returns:
        Decorator function that converts a function to a ChoiceFunction
        
    Example:
        ```python
        @choice.func(args=["greeting", "punctuation"])
        def greet(name: str, greeting="Hello", punctuation="!"):
            return f"{greeting} {name}{punctuation}"
        ```
    """
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
    """Decorator to create alternative implementations for choice functions.
    
    This decorator creates alternative implementations that can be used by
    rules to completely replace the behavior of a choice function in specific contexts.
    
    Args:
        implements: The ChoiceFunction this will be an implementation for
        args: List of parameter names this implementation accepts
        
    Returns:
        Decorator function that creates a ChoiceFuncImplementation
        
    Example:
        ```python
        @choice.impl(implements=greet, args=["greeting", "title"])
        def formal_greet(name: str, greeting="Dear", title=""):
            return f"{greeting} {title} {name}"
        ```
    """
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
    """Convert an existing function into a choice function implementation.
    
    This is a non-decorator alternative to @impl for when you want to convert
    an existing function into a choice implementation.
    
    Args:
        f: The function to convert
        implements: The ChoiceFunction this will implement
        args: List of parameter names this implementation accepts
        
    Returns:
        ChoiceFuncImplementation wrapping the provided function
        
    Example:
        ```python
        def existing_greet(name: str, style="casual"):
            return f"Hey {name}!"
            
        casual_impl = choice.wrap(existing_greet, greet, args=["style"])
        ```
    """
    return impl(implements, args=args)(f)


class ChoiceJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for PyChoice objects.
    
    This encoder handles serialization of PyChoice-specific objects like
    TraceItems, Traces, ChoiceFunctions, and Rules into JSON format.
    It's used primarily for trace serialization and debugging.
    
    Example:
        ```python
        trace_data = json.dumps(trace, cls=ChoiceJSONEncoder, indent=2)
        ```
    """
    def default(self, obj: Any) -> Any:
        """Convert PyChoice objects to JSON-serializable dictionaries.
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON-serializable representation of the object
        """
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
                "captures": obj.captures,
                "vals": {k: str(v) for k, v in obj.vals.items()},
            }
        try:
            return super().default(obj)
        except Exception:
            return type(obj).__name__
