"""MetaGraph node schema and kinds."""

from enum import Enum

NODE_SCHEMA = {
    "id": "string-UUID",
    "kind": "enum",
    "props": {"string": "any"},
    "edges": [{"type": "string", "to": "string-UUID"}],
    "prov": {"source": "path#span", "checksum": "sha256"},
}


class NodeKind(str, Enum):
    """Kinds of nodes used in the POC."""

    TABLE = "Table"
    COLUMN = "Column"
    STORY = "Story"
