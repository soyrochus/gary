"""Compute JSON-Patch between two graphs."""

from __future__ import annotations

import json
from typing import List

import networkx as nx


def diff_graphs(old: nx.MultiDiGraph, new: nx.MultiDiGraph) -> List[dict]:
    patch: List[dict] = []
    old_nodes = set(old.nodes)
    new_nodes = set(new.nodes)
    for node_id in sorted(new_nodes - old_nodes):
        patch.append({"op": "add", "path": "/nodes/-", "value": new.nodes[node_id]})
    for node_id in sorted(old_nodes - new_nodes):
        patch.append({"op": "remove", "path": f"/nodes/{node_id}"})
    old_edges = {(u, d["type"], v) for u, v, d in old.edges(data=True)}
    new_edges = {(u, d["type"], v) for u, v, d in new.edges(data=True)}
    for edge in sorted(new_edges - old_edges):
        patch.append({
            "op": "add",
            "path": "/edges/-",
            "value": {"from": edge[0], "type": edge[1], "to": edge[2]},
        })
    for edge in sorted(old_edges - new_edges):
        patch.append({"op": "remove", "path": f"/edges/{edge[0]}/{edge[1]}/{edge[2]}"})
    return patch
