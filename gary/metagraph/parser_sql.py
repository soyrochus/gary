"""Very small SQL DDL parser."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from .schema import NodeKind

CREATE_RE = re.compile(r"CREATE TABLE (\w+)(.*?)\);", re.S | re.I)
COLUMN_RE = re.compile(r"^\s*(\w+)", re.M)


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def parse_sql(path: Path) -> list[dict]:
    """Parse a SQL file into MetaGraph nodes."""
    text = path.read_text()
    nodes: list[dict] = []
    for table_match in CREATE_RE.finditer(text):
        table_name = table_match.group(1)
        block = table_match.group(0)
        table_id = str(uuid5(NAMESPACE_URL, f"Table:{table_name}"))
        table_node = {
            "id": table_id,
            "kind": NodeKind.TABLE.value,
            "props": {"name": table_name},
            "edges": [],
            "prov": {"source": f"{path}", "checksum": _checksum(block)},
        }
        nodes.append(table_node)
        for col_match in COLUMN_RE.finditer(table_match.group(2)):
            col_name = col_match.group(1)
            col_id = str(uuid5(NAMESPACE_URL, f"Column:{table_name}:{col_name}"))
            col_node = {
                "id": col_id,
                "kind": NodeKind.COLUMN.value,
                "props": {"name": col_name},
                "edges": [],
                "prov": {"source": f"{path}", "checksum": _checksum(col_name)},
            }
            nodes.append(col_node)
            table_node["edges"].append({"type": "has_column", "to": col_id})
    return nodes
