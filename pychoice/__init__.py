"""PyChoice: A library for managing choices, options, and configurations across abstraction hierarchy.

PyChoice provides a systematic way to customize function behavior through rules without 
modifying the original functions or breaking abstraction boundaries. It allows for 
complex configuration management and code injection patterns.

Basic usage:
    ```python
    import pychoice as choice
    
    @choice.func(args=["greeting"])
    def greet(name: str, greeting="Hello"):
        return f"{greeting} {name}"
    
    choice.rule([my_app, greet], greet, greeting="Hi")
    ```
"""

from .args import MissingChoiceArg
from .funcs import Match, Trace, def_rule, func, impl, registry, rule, trace_status, wrap
from .selector import ChoiceContext


def trace_start() -> None:
    """Start tracing choice function calls.
    
    Begins recording all choice function invocations and rule applications.
    Use this to debug and understand which choices are being made in your application.
    
    Example:
        ```python
        choice.trace_start()
        my_application()  # Run your code
        trace = choice.trace_stop()
        print(trace)  # See what choices were made
        ```
    """
    trace_status.start()


def trace_stop() -> Trace:
    """Stop tracing and return the collected trace data.
    
    Returns:
        Trace: A trace object containing all choice function calls and decisions
               made since trace_start() was called.
               
    Example:
        ```python
        choice.trace_start()
        my_application()
        trace = choice.trace_stop()
        trace.save("choices.json")  # Save for analysis
        ```
    """
    return trace_status.stop()


__all__ = [
    "ChoiceContext",
    "Match",
    "MissingChoiceArg",
    "def_rule",
    "func",
    "impl",
    "registry",
    "rule",
    "trace_start",
    "trace_stop",
    "wrap",
]
