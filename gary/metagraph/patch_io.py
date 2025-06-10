"""Read/write and apply JSON-Patch files."""

# --- v0.3 ADDITION ---
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx


def load_patch(path: Path) -> list[dict]:
    """Load an RFC-6902 patch from disk."""
    with path.open() as fh:
        return json.load(fh)


def dump_patch(patch: list[dict], path: Path) -> None:
    """Write patch to disk."""
    with path.open("w") as fh:
        json.dump(patch, fh, indent=2)


def apply_patch(graph: nx.MultiDiGraph, patch: list[dict]) -> None:
    """Apply add/remove operations to the graph."""
    for op in patch:
        if op["op"] == "add" and op["path"].startswith("/nodes"):
            node = op["value"]
            node_id = node["id"]
            graph.add_node(node_id, **node)
            for edge in node.get("edges", []):
                graph.add_edge(node_id, edge["to"], key=edge["type"], type=edge["type"])
        elif op["op"] == "add" and op["path"].startswith("/edges"):
            val = op["value"]
            graph.add_edge(val["from"], val["to"], key=val["type"], type=val["type"])
        elif op["op"] == "remove" and op["path"].startswith("/nodes"):
            node_id = op["path"].split("/")[-1]
            if graph.has_node(node_id):
                graph.remove_node(node_id)
        elif op["op"] == "remove" and op["path"].startswith("/edges"):
            _, u, typ, v = op["path"].split("/")
            if graph.has_edge(u, v, key=typ):
                graph.remove_edge(u, v, key=typ)
