import pychoice as choice

# Define functions


@choice.func()
def cfoo() -> str:
    return "foo"


@choice.func(implements=cfoo, args=["s"])
def cbar(s="bar") -> str:
    return s


# Tests


def test_cbar():
    assert cfoo() == "bar"


choice.rule([test_cbar, cfoo], cbar)


def test_cbaz():
    assert cfoo() == "baz"


choice.rule([test_cbaz, cfoo], cbar, s="baz")
