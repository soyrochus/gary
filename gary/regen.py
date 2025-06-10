"""Stub code generator walking the graph."""

from __future__ import annotations

from pathlib import Path

from .metagraph import load_graph


def regen(graph_path: Path, target: Path) -> None:
    graph = load_graph(graph_path)
    for node_id, data in graph.nodes(data=True):
        print(f"TODO generate for {data.get('kind')} {node_id} -> {target}")
