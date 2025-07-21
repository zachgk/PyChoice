import pychoice as choice

# Define functions


@choice.func_interface("cfoo")
def cfoo() -> str:
    return "foo"


@choice.func_impl("cfoo")
@choice.args("s")
def cbar(s="bar") -> str:
    return s


# Tests


choice.func_rule("cfoo", "test_cbar", "cbar")


def test_cbar():
    assert cfoo() == "bar"


choice.rule("cfoo", "test_cbaz", "cbar", s="baz")


def test_cbaz():
    assert cfoo() == "baz"
