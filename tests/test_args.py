import pytest

import pychoice as choice


@choice.args("greeting")
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"


def test_greet():
    assert greet("me") == "Hello me"
    assert "greet" in choice.registry
    assert "greeting" in choice.registry["greet"].defaults
    assert choice.registry["greet"].defaults["greeting"] == "Hello"


choice.arg_rule("greet", "test_override", greeting="Greetings")


def test_override():
    assert len(choice.registry["greet"].rules) > 0


def test_missing_choice_arg():
    with pytest.raises(choice.MissingChoiceArg):

        @choice.args("missing_arg")
        def echo(f):
            return f

        return echo
