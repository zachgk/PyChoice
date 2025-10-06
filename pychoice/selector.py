"""Selector system for PyChoice - matching patterns against call stacks.

This module provides the selector system used by PyChoice to match patterns
against function call stacks. It includes various types of selector items
that can match different kinds of callables (functions, methods, contexts)
and the infrastructure for managing choice contexts.
"""

from __future__ import annotations

import inspect
from contextvars import ContextVar
from types import TracebackType
from typing import Any, Callable, Optional, Union


class ChoiceContext:
    """Base class for choice contexts that provide temporary rule scoping.
    
    ChoiceContexts allow you to create temporary scopes where specific choice
    rules apply. They use Python's context manager protocol and context variables
    to track when they are active.
    
    Attributes:
        active: ContextVar tracking whether this context is currently active
        
    Example:
        ```python
        class DebugContext(ChoiceContext):
            pass
            
        with DebugContext():
            # Rules targeting DebugContext will apply here
            my_function()  # May use different implementation
        ```
    """
    active = ContextVar("active", default=False)

    def __enter__(self) -> None:
        self.active.set(True)

    def __exit__(
        self, exc_type: BaseException | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> bool | None:
        self.active.set(False)
        return None


class SelectorItem:
    """Abstract base class for items that can be used in choice selectors.
    
    SelectorItems define different ways to match against stack frames in
    choice function call stacks. Each type of SelectorItem implements
    different matching logic for various callable types.
    
    This is an abstract base class - use concrete subclasses like
    FunctionSelectorItem, ClassSelectorItem, or ChoiceContextSelectorItem.
    """
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    def get_callable(self) -> Callable[..., Any] | None:
        """Get the callable object this selector item represents.
        
        Returns:
            The callable object, or None if this item doesn't represent a callable
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        """Check if this selector item matches a stack frame.
        
        Args:
            frame_info: Stack frame to check for matching
            
        Returns:
            True if this selector item matches the frame, False otherwise
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError


SEL_I_CLS = tuple[type, str]
SEL_I = Union[Callable[..., Any], SEL_I_CLS, ChoiceContext, SelectorItem]
SEL = list[Callable[..., Any]]
StackFrame = list[inspect.FrameInfo]
OptStackFrame = Optional[StackFrame]

class InvalidSelectorItem(TypeError):
    """Exception raised when an invalid type is used as a selector item.
    
    This occurs when trying to create a SelectorItem from an object type
    that isn't supported by the selector system.
    
    Example:
        ```python
        # This would raise InvalidSelectorItem
        selector = Selector([my_func, 42])  # 42 is not a valid selector item
        ```
    """
    def __init__(self, item: SEL_I):
        """Initialize the exception with information about the invalid item.
        
        Args:
            item: The invalid selector item that caused the error
        """
        msg = f"Invalid selector item type: {type(item)} for {item}"
        super().__init__(msg)


class NonFunction(TypeError):
    """Exception raised when a non-function is used as final selector term.
    
    The final term in a selector must be a callable (typically a choice function)
    since it represents the target of the rule. This exception is raised when
    the final term is not callable.
    """
    def __init__(self) -> None:
        super().__init__("Expected a choice function for the final term in a selector")


class ChoiceContextSelectorItem(SelectorItem):
    """Selector item that matches when a specific ChoiceContext is active.
    
    This selector matches stack frames that occur while a particular
    ChoiceContext is active (i.e., within its context manager scope).
    
    Attributes:
        context: The ChoiceContext class to check for activity
        
    Example:
        ```python
        class DebugContext(ChoiceContext):
            pass
            
        debug_selector = ChoiceContextSelectorItem(DebugContext)
        # Matches when code runs within "with DebugContext():" blocks
        ```
    """
    def __init__(self, context: type[ChoiceContext]):
        """Initialize with a ChoiceContext class to match.
        
        Args:
            context: The ChoiceContext class that must be active for matching
        """
        self.context = context

    def __str__(self) -> str:
        return f"ChoiceContext(active={self.context.active.get()})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ChoiceContextSelectorItem) and self.context == other.context

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        """Check if the context is currently active.
        
        Args:
            frame_info: Stack frame (unused for context matching)
            
        Returns:
            True if the ChoiceContext is currently active, False otherwise
        """
        return self.context.active.get()


class FunctionSelectorItem(SelectorItem):
    """Selector item that matches specific function calls.
    
    This selector matches stack frames where the executing code corresponds
    to a specific function object, based on code object comparison.
    
    Attributes:
        func: The function to match against
        
    Example:
        ```python
        def my_function():
            pass
            
        func_selector = FunctionSelectorItem(my_function)
        # Matches stack frames executing my_function
        ```
    """
    def __init__(self, func: Callable[..., Any]):
        """Initialize with a function to match.
        
        Args:
            func: The function that this selector should match
        """
        self.func = func

    def __str__(self) -> str:
        return self.func.__name__

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FunctionSelectorItem) and self.func == other.func

    def get_callable(self) -> Callable[..., Any] | None:
        """Return the function this selector represents."""
        return self.func

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        """Check if the stack frame is executing this function.
        
        Args:
            frame_info: Stack frame to check
            
        Returns:
            True if the frame is executing this function, False otherwise
        """
        return self.func.__code__ == frame_info.frame.f_code


class CallableSelectorItem(SelectorItem):
    """Selector item that matches callable objects (including choice functions).
    
    This selector handles callable objects that may not be simple functions,
    such as choice functions, lambdas, or objects with __call__ methods.
    
    Attributes:
        func: The callable object to match against
        
    Example:
        ```python
        @choice.func()
        def my_choice_func():
            pass
            
        callable_selector = CallableSelectorItem(my_choice_func)
        # Matches stack frames executing the choice function
        ```
    """
    def __init__(self, func: Callable[..., Any]):
        """Initialize with a callable to match.
        
        Args:
            func: The callable object that this selector should match
        """
        self.func: Callable[..., Any] = func

    def __str__(self) -> str:
        return self.func.__name__

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CallableSelectorItem) and self.func == other.func

    def get_callable(self) -> Callable[..., Any] | None:
        """Return the callable this selector represents."""
        return self.func

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        """Check if the stack frame is executing this callable.
        
        This method handles the complexity of matching callable objects,
        including checking code objects and instance matching for methods.
        
        Args:
            frame_info: Stack frame to check
            
        Returns:
            True if the frame is executing this callable, False otherwise
        """
        if not hasattr(self.func.__call__, "__code__"):  # type: ignore[operator]
            return False
        if self.func.__call__.__code__ != frame_info.frame.f_code:  # type: ignore[operator]
            return False
        return not (hasattr(self.func, "__class__") and self.func != frame_info.frame.f_locals.get("self", None))


class ClassSelectorItem(SelectorItem):
    """Selector item that matches specific class methods.
    
    This selector matches stack frames where a specific method of a specific
    class (or its subclasses) is being executed. It supports inheritance
    matching.
    
    Attributes:
        cls: The class to match
        qual_name: Qualified name string (ClassName.method_name)
        func_name: Name of the method to match
        
    Example:
        ```python
        class MyClass:
            def my_method(self):
                pass
                
        class_selector = ClassSelectorItem(MyClass, "my_method")
        # Matches when MyClass.my_method or subclass.my_method is executing
        ```
    """
    def __init__(self, cls: type, func_name: str):
        """Initialize with a class and method name to match.
        
        Args:
            cls: The class that must contain the method
            func_name: Name of the method to match
        """
        self.cls = cls
        self.qual_name = f"{cls.__name__}.{func_name}"
        self.func_name = func_name

    def __str__(self) -> str:
        return self.qual_name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ClassSelectorItem) and self.cls == other.cls and self.func_name == other.func_name

    def matches(self, frame_info: inspect.FrameInfo) -> bool:
        """Check if the stack frame is executing this class method.
        
        This method checks both the method name and class hierarchy,
        supporting inheritance matching where subclass methods match
        their parent class selectors.
        
        Args:
            frame_info: Stack frame to check
            
        Returns:
            True if frame is executing this class method or a subclass override
        """
        if frame_info.frame.f_code.co_name == self.func_name:
            qualname = frame_info.frame.f_code.co_qualname
            parts = qualname.split(".")
            if len(parts) > 1:
                class_name = parts[0]
                module = inspect.getmodule(frame_info.frame)
                cls = getattr(module, class_name, None)
                if not isinstance(cls, type):
                    return False
                return cls == self.cls or issubclass(cls, self.cls)
        return False
