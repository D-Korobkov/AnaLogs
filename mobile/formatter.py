import pathlib
from typing import List

from graphviz import Digraph

from mobile.model import LogNode


def visualize_dot(nodes: List[LogNode], out: pathlib.Path):
    dot = Digraph(comment="A Logs Graph")
    dot.attr(rankdir="TB")

    for parent_index, parent_node in enumerate(nodes):
        with dot.subgraph() as sub:
            sub.node(parent_node.get_node_id(), str(parent_node), shape="rectangle")

            if parent_index != 0:
                dot.edge(
                    nodes[parent_index - 1].get_node_id(),
                    parent_node.get_node_id(),
                    color="red",
                    constraint="false",
                )

            for child_index, child_node in enumerate(parent_node.children):
                sub.node(child_node.get_node_id(), str(child_node))

                if child_index == 0:
                    sub.edge(parent_node.get_node_id(), child_node.get_node_id())

                else:
                    sub.edge(
                        parent_node.children[child_index - 1].get_node_id(),
                        child_node.get_node_id(),
                    )

    dot.format = "png"
    dot.render(out, view=True)
