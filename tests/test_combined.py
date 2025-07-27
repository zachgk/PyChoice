import pychoice as choice

# Define functions


@choice.func_interface()
def cfoo() -> str:
    return "foo"


@choice.func_impl(cfoo)
@choice.args("s")
def cbar(s="bar") -> str:
    return s


# Tests


def test_cbar():
    assert cfoo() == "bar"


choice.func_rule([test_cbar, cfoo], cbar)


def test_cbaz():
    assert cfoo() == "baz"


choice.rule([test_cbaz, cfoo], cbar, s="baz")
