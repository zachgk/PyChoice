import networkx as nx
import matplotlib.pyplot as plt
from typing import Optional

from .selector import SEL, selector_generic_compare

def build_selector_poset(selectors: list[SEL]) -> nx.DiGraph:
    """
    Build a directed graph representing the poset of selectors.
    An edge from A to B means A is a sub-selector of B.
    Transitive edges are pruned for clarity.
    """
    G: nx.DiGraph = nx.DiGraph()
    # Add nodes
    for sel in selectors:
        label = str([f.__name__ for f in sel])
        G.add_node(label)
    # Add edges
    for i, a in enumerate(selectors):
        for j, b in enumerate(selectors):
            if i == j:
                continue
            cmp = selector_generic_compare(a, b)
            if cmp == 1:
                # a is sub-selector of b
                label_a = str([f.__name__ for f in a])
                label_b = str([f.__name__ for f in b])
                G.add_edge(label_a, label_b)
    # Prune transitive edges
    G = nx.algorithms.dag.transitive_reduction(G)
    return G

def visualize_selector_poset(selectors: list[SEL], filename: Optional[str] = None) -> None:
    """
    Visualize a poset graph for the given selectors.
    """
    G = build_selector_poset(selectors)
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=1500, node_color='lightblue', arrows=True)

    if filename is not None:
        plt.savefig(filename)
    else:
        plt.show()