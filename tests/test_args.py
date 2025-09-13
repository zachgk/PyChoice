import pytest

import pychoice as choice


@choice.func(args=["greeting"])
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"


def wrap_greet(name: str):
    return greet(name)


def test_registry_entry():
    assert "greet" in [f.interface.func.__name__ for f in choice.registry]


def test_greet():
    choice.trace_start()
    assert greet("me") == "Hello me"
    trace = choice.trace_stop()
    print(trace)
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


choice.def_rule([test_cap, choice.Match(wrap_greet, ["name"]), greet])(
    lambda c: (greet, {"greeting": f"Greetings {c['name']}"})
)
choice.def_rule([test_cap, greet])(lambda c: None)  # Also test None return


def test_def_rule():
    assert wrap_greet("me") == "Greetings me me"


@choice.def_rule([test_def_rule, choice.Match(wrap_greet, ["name"]), greet])
def rule_test_def_rule(captures):
    """Rule for test_def_rule"""
    return greet, {"greeting": f"Greetings {captures['name']}"}


def test_match_choice_function():
    assert greet("dog") == "What's up dog"


@choice.def_rule([choice.Match(greet, ["name"])])
def rule_test_match_choice_function(captures):
    if "name" in captures and captures["name"] == "dog":
        return (greet, {"greeting": "What's up"})
    return None
