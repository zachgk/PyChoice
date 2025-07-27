from typing import Any, Callable

from .args import arg_rule
from .funcs import func_rule
from .selector import SEL


def rule(selector: SEL, impl: Callable[..., Any], **kwargs: dict[str, Any]) -> None:
    func_rule(selector, impl)
    arg_rule(selector[:-1] + [impl], **kwargs)
