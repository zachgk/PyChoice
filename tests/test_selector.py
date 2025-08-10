import networkx as nx
import pytest

from pychoice.poset import build_selector_poset, visualize_selector_poset
from pychoice.selector import Selector

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
        assert Selector([foo]).generic_compare(Selector([foo])) == 0

    def test_gt(self):
        assert Selector([baz, foo]).generic_compare(Selector([foo])) == -1

    def test_lt(self):
        assert Selector([foo]).generic_compare(Selector([baz, foo])) == 1

    def test_unrelated(self):
        assert Selector([foo]).generic_compare(Selector([bar])) == 0


test_selectors_raw = [
    [foo],
    [bar, foo],
    [baz, bar, foo],
    [baz, foo],
]
test_selectors = [Selector(sel) for sel in test_selectors_raw]


class TestSelectorPoset:
    def test_build_selector_poset(self):
        poset = build_selector_poset(test_selectors)
        assert len(poset.nodes) == 4
        assert len(poset.edges) == 3
        text_lines = nx.generate_network_text(poset)
        text_string = "\n".join(text_lines)
        print(text_string)

    @pytest.mark.skip
    def test_visualize_selector_poset(self):
        visualize_selector_poset(test_selectors, filename="test_poset.png")
        # This will display the graph, no assertion needed
        # Just ensure it runs without error
        assert True
