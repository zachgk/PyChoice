from .args import MissingChoiceArg
from .funcs import Match, Trace, def_rule, func, impl, registry, rule, trace_status, wrap
from .selector import ChoiceContext


def trace_start() -> None:
    trace_status.start()


def trace_stop() -> Trace:
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
