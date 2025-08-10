from typing import Optional

import matplotlib.pyplot as plt
import networkx as nx

from .selector import Selector


def build_selector_poset(selectors: list[Selector]) -> nx.DiGraph:
    """
    Build a directed graph representing the poset of selectors.
    An edge from A to B means A is a sub-selector of B.
    Transitive edges are pruned for clarity.
    """
    G: nx.DiGraph = nx.DiGraph()
    # Add nodes
    for sel in selectors:
        G.add_node(str(sel))
    # Add edges
    for i, a in enumerate(selectors):
        for j, b in enumerate(selectors):
            if i == j:
                continue
            cmp = a.generic_compare(b)
            if cmp == 1:
                # a is sub-selector of b
                G.add_edge(str(a), str(b))
    # Prune transitive edges
    G = nx.algorithms.dag.transitive_reduction(G)
    return G


def visualize_selector_poset(selectors: list[Selector], filename: Optional[str] = None) -> None:
    """
    Visualize a poset graph for the given selectors.
    """
    G = build_selector_poset(selectors)
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=1500, node_color="lightblue", arrows=True)

    if filename is not None:
        plt.savefig(filename)
    else:
        plt.show()
