import pytest

import pychoice as choice


@choice.args("greeting")
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"


def registry_entry():
    assert "greet" in choice.registry


def test_greet():
    assert greet("me") == "Hello me"
    assert "greeting" in greet.defaults
    assert greet.defaults["greeting"] == "Hello"


def test_override():
    assert greet.rule_selectors[0][0].__name__ == "test_override"
    assert greet("me") == "Greetings me"


choice.arg_rule([test_override, greet], greeting="Greetings")


def test_override2():
    assert greet.rule_selectors[1][0].__name__ == "test_override2"
    assert greet("me") == "Greetings2 me"


choice.arg_rule([test_override2, greet], greeting="Greetings2")


def test_missing_choice_arg():
    with pytest.raises(choice.MissingChoiceArg):

        @choice.args("missing_arg")
        def echo(f):
            return f

        return echo
