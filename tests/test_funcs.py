import pychoice as choice

# Define functions


@choice.func_interface()
def foo() -> str:
    return "foo"


@choice.func_impl(foo)
def bar() -> str:
    return "bar"


@choice.func_impl(foo)
def baz() -> str:
    return "baz"


# Tests


def test_base_interface():
    assert foo() == "foo"


def test_bar():
    assert foo() == "bar"


choice.func_rule([test_bar, foo], bar)


def test_baz():
    assert foo() == "baz"


choice.func_rule([test_baz, foo], baz)


def wrap_foo():
    return foo()


def test_override_override():
    assert wrap_foo() == "baz"


choice.func_rule([wrap_foo, foo], bar)
choice.func_rule([test_override_override, wrap_foo, foo], baz)
