import pytest

import pychoice as choice


@choice.args("greeting")
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"


def test_greet():
    assert greet("me") == "Hello me"
    assert "greet" in choice.registry
    assert "greeting" in choice.registry["greet"]
    assert choice.registry["greet"]["greeting"] == "Hello"


def test_missing_choice_arg():
    with pytest.raises(choice.MissingChoiceArg):

        @choice.args("missing_arg")
        def echo(f):
            return f

        return echo
