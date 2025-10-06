"""Poset (Partially Ordered Set) visualization for PyChoice selectors.

This module provides tools for analyzing and visualizing the relationships
between choice selectors. It builds directed graphs representing the poset
structure of selectors, where edges indicate sub-selector relationships,
helping developers understand rule precedence and specificity.

The poset visualization is particularly useful for debugging complex choice
rule hierarchies and understanding how different selectors relate to each other.
"""

from typing import Optional

import matplotlib.pyplot as plt
import networkx as nx

from .args import Selector


def build_selector_poset(selectors: list[Selector]) -> nx.DiGraph:
    """Build a directed graph representing the partial order of selectors.

    Creates a directed acyclic graph (DAG) where nodes represent selectors
    and edges represent sub-selector relationships. An edge from A to B
    indicates that A is a sub-selector of B (A is more specific than B).

    The resulting graph has transitive edges removed for clarity, showing
    only the direct relationships between selectors in the hierarchy.

    Args:
        selectors: List of Selector objects to analyze

    Returns:
        NetworkX DiGraph representing the selector poset with transitive
        reduction applied for visual clarity

    Example:
        ```python
        selectors = [
            Selector([app]),
            Selector([app, module]),
            Selector([app, module, func])
        ]
        graph = build_selector_poset(selectors)
        # Graph shows: [app, module, func] -> [app, module] -> [app]
        ```
    """
    G: nx.DiGraph = nx.DiGraph()

    # Add nodes (each selector becomes a node)
    for sel in selectors:
        G.add_node(str(sel))

    # Add edges based on sub-selector relationships
    for i, a in enumerate(selectors):
        for j, b in enumerate(selectors):
            if i == j:
                continue
            cmp = a.generic_compare(b)
            if cmp == 1:
                # a is a sub-selector of b (more specific than b)
                G.add_edge(str(a), str(b))

    # Remove transitive edges for clearer visualization
    # This keeps only direct parent-child relationships
    G = nx.algorithms.dag.transitive_reduction(G)
    return G


def visualize_selector_poset(selectors: list[Selector], filename: Optional[str] = None) -> None:
    """Visualize the poset structure of selectors as a graph diagram.

    Creates a visual representation of selector relationships using matplotlib
    and NetworkX. The graph shows the hierarchy of selectors with arrows
    indicating sub-selector relationships (from more specific to less specific).

    This visualization helps in understanding:
    - Which selectors are more specific than others
    - The overall hierarchy of choice rules
    - Potential conflicts or overlapping rules
    - The precedence order that will be used at runtime

    Args:
        selectors: List of Selector objects to visualize
        filename: Optional path to save the visualization. If None, displays interactively

    Example:
        ```python
        from pychoice.poset import visualize_selector_poset

        # Create some selectors
        selectors = [
            Selector([my_app, greet]),
            Selector([my_app, email_module, greet]),
            Selector([my_app, email_module, formal_context, greet])
        ]

        # Visualize and save to file
        visualize_selector_poset(selectors, "selector_hierarchy.png")

        # Or display interactively
        visualize_selector_poset(selectors)
        ```

    Note:
        Requires matplotlib and networkx to be installed. The visualization
        uses a spring layout algorithm to position nodes, so the exact
        layout may vary between runs but the relationships will be consistent.
    """
    G = build_selector_poset(selectors)
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=1500, node_color="lightblue", arrows=True)

    if filename is not None:
        plt.savefig(filename)
    else:
        plt.show()
