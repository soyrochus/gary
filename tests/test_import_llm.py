import asyncio
import json

import openai

from gary.metagraph import importer_llm


class DummyResp:
    def __init__(self, data):
        self.choices = [{"message": {"function_call": {"arguments": json.dumps(data)}}}]


async def fake_acreate(*args, **kwargs):
    return DummyResp({"nodes": [{"id": "1", "kind": "Story", "props": {}, "edges": [], "prov": {}}], "errors": []})


def test_import_llm(monkeypatch, tmp_path):
    monkeypatch.setattr(openai.ChatCompletion, "acreate", fake_acreate)
    path = tmp_path / "a.dsl"
    path.write_text("foo")
    nodes = asyncio.run(importer_llm.import_with_llm(path))
    assert nodes and nodes[0]["id"] == "1"

