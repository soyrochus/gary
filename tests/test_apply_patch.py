import networkx as nx

from gary.metagraph import graph_io, patch_io, validation


def test_apply_patch(tmp_path):
    graph_path = tmp_path / "g.graphson"
    graph_io.dump_graph(nx.MultiDiGraph(), graph_path)
    patch = [{"op": "add", "path": "/nodes/-", "value": {"id": "1", "kind": "Story", "props": {}, "edges": [], "prov": {}}}]
    graph = graph_io.load_graph(graph_path)
    patch_io.apply_patch(graph, patch)
    validation.validate_graph(graph)
    assert len(graph.nodes) == 1

