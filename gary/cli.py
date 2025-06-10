"""Command line interface for Gary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .metagraph import (
    diff_graphs,
    dump_graph,
    load_graph,
    parse_md,
    parse_sql,
    patch_io,
    importer_core,
    validation,
    # --- v0.3 ADDITION ---
)
from .regen import regen


def build_cmd(args: argparse.Namespace) -> None:
    graph = load_graph(Path(args.output)) if Path(args.output).exists() else None
    if graph is None:
        import networkx as nx

        graph = nx.MultiDiGraph()
    for file in args.files:
        path = Path(file)
        if path.suffix.lower().endswith(".sql"):
            nodes = parse_sql(path)
        elif path.suffix.lower() in {".md", ".markdown"}:
            nodes = parse_md(path)
        else:
            continue
        for node in nodes:
            node_id = node["id"]
            graph.add_node(node_id, **node)
            for edge in node.get("edges", []):
                graph.add_edge(node_id, edge["to"], key=edge["type"], type=edge["type"])
    dump_graph(graph, Path(args.output))


def show_cmd(args: argparse.Namespace) -> None:
    graph = load_graph(Path(args.graphson))
    kinds: dict[str, list[str]] = {}
    for node_id, data in graph.nodes(data=True):
        kinds.setdefault(data.get("kind"), []).append(node_id)
    for kind, ids in kinds.items():
        print(f"{kind} ({len(ids)})")
        for node_id in ids:
            print("  ", node_id)


def diff_cmd(args: argparse.Namespace) -> None:
    old = load_graph(Path(args.old))
    new = load_graph(Path(args.new))
    patch = diff_graphs(old, new)
    print(json.dumps(patch, indent=2))


def regen_cmd(args: argparse.Namespace) -> None:
    regen(Path(args.graphson), Path(args.target))


# --- v0.3 ADDITION ---
def import_cmd(args: argparse.Namespace) -> None:
    import asyncio
    patch = asyncio.run(importer_core.import_files([Path(f) for f in args.files]))
    if args.output:
        patch_io.dump_patch(patch, Path(args.output))
    else:
        print(json.dumps(patch, indent=2))

# --- v0.3 ADDITION ---
def apply_cmd(args: argparse.Namespace) -> None:
    graph = load_graph(Path("metagraph.graphson"))
    patch = patch_io.load_patch(Path(args.patch))
    patch_io.apply_patch(graph, patch)
    validation.validate_graph(graph)
    dump_graph(graph, Path("metagraph.graphson"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gary", description="Gary CLI")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="build metagraph")
    p_build.add_argument("files", nargs="+")
    p_build.add_argument("-o", "--output", default="metagraph.graphson")
    p_build.set_defaults(func=build_cmd)

    p_show = sub.add_parser("show", help="show graph")
    p_show.add_argument("graphson")
    p_show.set_defaults(func=show_cmd)

    p_diff = sub.add_parser("diff", help="diff two graphs")
    p_diff.add_argument("old")
    p_diff.add_argument("new")
    p_diff.set_defaults(func=diff_cmd)

    p_regen = sub.add_parser("regen", help="regenerate stubs")
    p_regen.add_argument("graphson")
    p_regen.add_argument("target")
    p_regen.set_defaults(func=regen_cmd)

    p_import = sub.add_parser("import", help="import artefact")
    p_import.add_argument("files", nargs="+")
    p_import.add_argument("-o", "--output")
    p_import.set_defaults(func=import_cmd)

    p_apply = sub.add_parser("apply", help="apply patch")
    p_apply.add_argument("patch")
    p_apply.set_defaults(func=apply_cmd)

    args = parser.parse_args(argv)
    args.func(args)
    return 0
