import pychoice as choice
from pychoice.selector import selector_generic_compare

# Define functions

def foo() -> str:
    return "foo"


def bar() -> str:
    return "bar"


def baz() -> str:
    return "baz"


# Tests

class TestSelectorGenericCompare:
    def test_eq(self):
        assert selector_generic_compare([foo], [foo]) == 0

    def test_gt(self):
        assert selector_generic_compare([baz, foo], [foo]) == -1

    def test_lt(self):
        assert selector_generic_compare([foo], [baz, foo]) == 1

    def test_unrelated(self):
        assert selector_generic_compare([foo], [bar]) == 0