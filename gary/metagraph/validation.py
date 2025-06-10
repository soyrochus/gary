"""Validation helpers for MetaGraph."""

# --- v0.3 ADDITION ---
from __future__ import annotations

from jsonschema import validate
import networkx as nx

from .schema import NODE_SCHEMA


def validate_graph(graph: nx.MultiDiGraph) -> None:
    """Validate all nodes against the NODE_SCHEMA."""
    for _, data in graph.nodes(data=True):
        validate(instance=data, schema=NODE_SCHEMA)
