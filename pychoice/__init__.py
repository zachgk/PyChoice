from .args import MissingChoiceArg
from .funcs import cap_rule, def_rule, func, registry, rule, trace_status
from .selector import Match
from .trace import Trace


def trace_start() -> None:
    trace_status.start()


def trace_stop() -> Trace:
    return trace_status.stop()


__all__ = ["Match", "MissingChoiceArg", "cap_rule", "def_rule", "func", "registry", "rule", "trace_start", "trace_stop"]
