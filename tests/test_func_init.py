import pychoice as choice

# Define functions


class Foo:
    def foo(self) -> str:
        return "foo"


@choice.func()
def cfoo() -> Foo:
    return Foo()


def test_foo():
    assert cfoo().foo() == "foo"


# Using a class as an implementation


@choice.impl(implements=cfoo)
class Bar(Foo):
    def foo(self) -> str:
        return "bar"


def test_bar():
    assert cfoo().foo() == "bar"


choice.rule([test_bar, cfoo], Bar)


@choice.impl(implements=cfoo, args=["arg"])
class ArgBar(Foo):
    def __init__(self, arg: str):
        self.arg = arg

    def foo(self) -> str:
        return f"bar-{self.arg}"


def test_arg_bar():
    assert cfoo().foo() == "bar-arg"


choice.rule([test_arg_bar, cfoo], ArgBar, arg="arg")
