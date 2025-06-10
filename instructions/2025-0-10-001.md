SYSTEM
You are an experienced software engineer.  
Your task: generate a runnable proof-of-concept (POC) for **Gary v0.2**.

## Vision
* **Gary** = playful sandbox, CLI, eventual UI, LangGraph agent host.  
* **MetaGraph** = internal module that holds a property-graph IR used by Gary.

## Mandatory constraints
1. **Language**: Python 3.12; only stdlib + `networkx` + `jsonschema`.  
2. **Graph serialisation**: newline-delimited GraphSON v2 (`metagraph.graphson`).  
3. **MetaGraph node schema** (JSON Schema):  
   ```json
   {
     "id": "string-UUID",
     "kind": "enum",
     "props": { "string": any },
     "edges": [ { "type": "string", "to": "string-UUID" } ],
     "prov": { "source": "path#span", "checksum": "sha256" }
   }
   ```

4. **POC scope**

   * Parse **SQL DDL** and **Markdown User Story** samples.
   * Build graph, write & reload.
   * Provide CLI: `gary build …`, `gary show …`, `gary diff old new`.
   * `diff` prints RFC-6902 JSON-Patch for node/edge adds/removes.

## Repo layout

```
<<project_root>>/
 ├─ gary/
 │   ├─ __init__.py
 │   ├─ __main__.py         # exposes CLI entrypoint
 │   ├─ cli.py              # argparse commands: build/show/diff
 │   ├─ metagraph/          # internal IR implementation
 │   │   ├─ __init__.py
 │   │   ├─ schema.py       # JSON Schema + enum
 │   │   ├─ parser_sql.py   # simple regex parser
 │   │   ├─ parser_md.py
 │   │   ├─ graph_io.py     # GraphSON read/write helpers
 │   │   └─ diff.py         # produces JSON-Patch
 │   └─ regen.py            # stub generator (walks graph, prints TODO)
 ├─ samples/
 │   ├─ sql/schema.sql
 │   └─ stories/login.md
 ├─ tests/                  # pytest smoke tests (optional)
 └─ README.md               # **reuse existing README content**
```

## Parsing tips

* SQL: regex `CREATE TABLE (\w+)` and column lines.
* Markdown: first `#` heading → Story node (`Story`), body lines → props.

## IDs & checksums

* Deterministic: `uuid5(NAMESPACE_URL, f"{kind}:{name}")`.
* `checksum`: SHA-256 of source text slice.

## Diff algorithm

1. Load both graphs into `networkx.MultiDiGraph`.
2. Node diff = ID set difference.
3. Edge diff = tuple `(from, type, to)`.
4. Emit JSON-Patch: `{ "op":"add", "path":"/nodes/-", "value":{…} }`.

## CLI usage to satisfy README

```bash
uv run python -m gary build samples/sql/schema.sql samples/stories/login.md
uv run python -m gary show metagraph.graphson
uv run python -m gary diff metagraph.graphson new.graphson
```

## Deliverables

Return multi-file output using correctly labelled code fences, exactly matching the repo layout.
Leave the README intact apart from any needed changes related to this prompt.

Return **only** the file contents—no extra commentary.
