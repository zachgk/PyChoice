import pychoice as choice

# Define functions


@choice.func_interface("foo")
def foo() -> str:
    return "foo"


@choice.func_impl("foo")
def bar() -> str:
    return "bar"


@choice.func_impl("foo")
def baz() -> str:
    return "baz"


# Tests


def test_base_interface():
    assert foo() == "foo"


choice.func_rule("foo", "test_bar", "bar")


def test_bar():
    assert foo() == "bar"


choice.func_rule("foo", "test_baz", "baz")


def test_baz():
    assert foo() == "baz"
