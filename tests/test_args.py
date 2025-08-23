import pytest

import pychoice as choice


@choice.func(args=["greeting"])
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"


def wrap_greet(name: str):
    return greet(name)


def test_registry_entry():
    assert "greet" in choice.registry


def test_greet():
    choice.trace_start()
    assert greet("me") == "Hello me"
    trace = choice.trace_stop()
    assert trace.count == 1
    assert len(trace.items) == 1
    assert len(trace.items[0].items) == 0


def test_override():
    assert greet("me") == "Greetings me"


choice.rule([test_override, greet], greet, greeting="Greetings")


def test_override2():
    assert greet.rules[1].selector.items[0].func.__name__ == "test_override2"
    assert greet("me") == "Greetings2 me"


choice.rule([test_override2, greet], greet, greeting="Greetings2")


def test_override_override():
    assert wrap_greet("me") == "Greetings me"


choice.rule([wrap_greet, greet], greet, greeting="Wrap")
choice.rule([test_override_override, wrap_greet, greet], greet, greeting="Greetings")


def test_missing_choice_arg():
    with pytest.raises(choice.MissingChoiceArg):

        @choice.func(args=["missing_arg"])
        def echo(f):
            return f

        return echo


def test_cap():
    assert wrap_greet("me") == "Greetings me me"


choice.cap_rule(
    [test_cap, choice.Match(wrap_greet, ["name"]), greet], greet, lambda c: {"greeting": f"Greetings {c['name']}"}
)


def test_def_rule():
    assert wrap_greet("me") == "Greetings me me"


@choice.def_rule([test_def_rule, choice.Match(wrap_greet, ["name"]), greet], greet)
def rule_test_def_rule(captures):
    return {"greeting": f"Greetings {captures['name']}"}
