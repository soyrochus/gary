"""Importer orchestrating deterministic and LLM paths."""

# --- v0.3 ADDITION ---
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Literal

import networkx as nx

from .diff import diff_graphs
from .parser_sql import parse_sql
from .parser_md import parse_md
from .importer_llm import import_with_llm

CACHE_DIR = Path(".cache/import")


def choose_importer(path: Path) -> Literal["deterministic", "llm"]:
    if path.suffix in {".sql", ".md"} and path.stat().st_size <= 16_384:
        return "deterministic"
    return "llm"


async def import_file(path: Path) -> list[dict]:
    """Return patch operations for a single artefact."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    cache_path = CACHE_DIR / f"{file_hash}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    if choose_importer(path) == "deterministic":
        nodes = parse_sql(path) if path.suffix == ".sql" else parse_md(path)
    else:
        nodes = await import_with_llm(path)
    base = nx.MultiDiGraph()
    new = nx.MultiDiGraph()
    for node in nodes:
        node_id = node["id"]
        new.add_node(node_id, **node)
        for edge in node.get("edges", []):
            new.add_edge(node_id, edge["to"], key=edge["type"], type=edge["type"])
    patch = diff_graphs(base, new)
    cache_path.write_text(json.dumps(patch))
    return patch


async def import_files(paths: list[Path]) -> list[dict]:
    patch: list[dict] = []
    for path in paths:
        patch.extend(await import_file(path))
    return patch
