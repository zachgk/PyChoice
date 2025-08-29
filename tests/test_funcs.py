import pychoice as choice

# Define functions


@choice.func()
def foo() -> str:
    return "foo"


@choice.func(implements=foo)
def bar() -> str:
    return "bar"


@choice.func(implements=foo)
def baz() -> str:
    return "baz"


# Tests


def test_base_interface():
    assert foo() == "foo"


def test_bar():
    assert foo() == "bar"


choice.rule([test_bar, foo], bar)


def test_baz():
    assert foo() == "baz"


choice.rule([test_baz, foo], baz)


def wrap_foo():
    return foo()


def test_override_override():
    assert wrap_foo() == "baz"


choice.rule([wrap_foo, foo], bar)
choice.rule([test_override_override, wrap_foo, foo], baz)


def buzz() -> str:
    return "buzz"


wrap_buzz = choice.wrap(buzz, implements=foo)


def test_wrap():
    assert foo() == "buzz"


choice.rule([test_wrap, foo], wrap_buzz)


class TestClasses:
    def test_class_override(self):
        assert foo() == "bar"


choice.rule([(TestClasses, "test_class_override"), foo], bar)


class ParentClass:
    pass


class TestChildClass(ParentClass):
    def test_child_class_override(self):
        assert foo() == "bar"


choice.rule([(ParentClass, "test_child_class_override"), foo], bar)
