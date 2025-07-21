from typing import Any

from .args import arg_rule
from .funcs import func_rule


def rule(interface: str, selector: str, impl: str, **kwargs: dict[str, Any]) -> None:
    func_rule(interface, selector, impl)
    arg_rule(impl, selector, **kwargs)
