"""Simple Markdown user story parser."""

from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from .schema import NodeKind


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def parse_md(path: Path) -> list[dict]:
    """Parse a Markdown file into a Story node."""
    text = path.read_text()
    title = None
    body_lines: list[str] = []
    for line in text.splitlines():
        if title is None and line.startswith("#"):
            title = line.lstrip("# ").strip()
        else:
            body_lines.append(line)
    if title is None:
        return []
    story_id = str(uuid5(NAMESPACE_URL, f"Story:{title}"))
    node = {
        "id": story_id,
        "kind": NodeKind.STORY.value,
        "props": {"title": title, "body": "\n".join(body_lines).strip()},
        "edges": [],
        "prov": {"source": f"{path}", "checksum": _checksum(text)},
    }
    return [node]
