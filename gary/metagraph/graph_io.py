"""GraphSON read/write helpers."""

from __future__ import annotations

import json
from pathlib import Path

import networkx as nx


def load_graph(path: Path) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    if not path.exists():
        return graph
    with path.open() as fh:
        for line in fh:
            data = json.loads(line)
            node_id = data["id"]
            graph.add_node(node_id, **data)
            for edge in data.get("edges", []):
                graph.add_edge(node_id, edge["to"], key=edge["type"], type=edge["type"])
    return graph


def dump_graph(graph: nx.MultiDiGraph, path: Path) -> None:
    with path.open("w") as fh:
        for node_id, data in graph.nodes(data=True):
            edges = [
                {"type": d["type"], "to": v}
                for _, v, d in graph.edges(node_id, data=True)
            ]
            out = {
                "id": node_id,
                "kind": data.get("kind"),
                "props": data.get("props", {}),
                "edges": edges,
                "prov": data.get("prov", {}),
            }
            fh.write(json.dumps(out) + "\n")
