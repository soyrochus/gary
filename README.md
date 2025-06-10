# Gary ­– A Test Bed for MetaGraph-Powered LangGraph Agents  
*(Same hardy snail, brand-new brain.)*

Gary started life as a quirky Swing-to-NiceGUI converter.  
He’s now pivoting into a **sandbox for experimenting with a graph-based Intermediate Representation (IR) called _MetaGraph_**.  
The end-goal is identical—AI-assisted code generation—but the path now runs through a property-graph hub that merges every artefact we can throw at it.

![Gary](img/gary_small.png)

## What Gary does (v0.2.0)

| Stage | Purpose | Current status |
|-------|---------|----------------|
| **Multi-parse** | Ingest heterogeneous artefacts and emit MetaGraph nodes/edges. <br>• _DDL → Table/Column nodes_ <br>• _Markdown stories → Story nodes_ | ✅ Regex POC parsers included |
| **Graph store** | Persist MetaGraph as newline-delimited **GraphSON v2** (`metagraph.graphson`). | ✅ networkx + JSON streaming |
| **Diff & patch** | CLI sub-command produces an **RFC-6902 JSON-Patch** between two graph versions. | ✅ Minimal GumTree-style diff |
| **Regenerate** | Stub generators walk the cleaned graph to (eventually) spit out code/tests/UI. | ⚠️ Hook provided; real templates TBD |
| **LLM play-pen** | Future: LangGraph agents propose semantic patches instead of raw code. | 🛣️ Road-map item |

## Installation

1. **Clone & enter**  
   ```bash
   git clone https://github.com/yourusername/gary.git
   cd gary
   ```

2. **Set up with `uv`** *(fast Poetry-like manager)*

   ```bash
   uv sync
   ```

3. **API keys (optional, for later agent work)**

   ```bash
   echo "OPENAI_API_KEY=sk-..." > .env        # keep in .gitignore
   echo "OPENAI_MODEL=gpt-4o-mini" >> .env
   ```

> **Prereqs**: Python 3.12+, `uv` 0.1.36+, `pip install networkx jsonschema` if you prefer pip.

## Quick-start

### Build a MetaGraph from sample artefacts

```bash
uv run python -m gary build samples/sql/schema.sql samples/stories/login.md
```

Creates `metagraph.graphson` in the project root.

### Visualise the graph (one-liner)

```bash
uv run python -m gary show metagraph.graphson
```

### Make a change → diff it

```bash
# pretend we edited schema.sql to add a column
uv run python -m gary build samples/sql/schema.sql > new.graphson
uv run python -m gary diff metagraph.graphson new.graphson
# → prints JSON-Patch with added node + edge
```

## Importing artefacts

```bash
uv run python -m gary import samples/xml/widget.xml -o patch.json
uv run python -m gary apply patch.json
```

The `import` command chooses between deterministic parsers and an LLM-based path.
The `apply` command merges the resulting patch into `metagraph.graphson` after validation.


## Command overview

| Command                         | What it does                                           |
| ------------------------------- | ------------------------------------------------------ |
| `build <files…>`                | Parse inputs, merge into MetaGraph, write `.graphson`. |
| `show  <graphson>`              | Pretty-print nodes & edges grouped by `kind`.          |
| `diff  <old> <new>`             | Output JSON-Patch for node/edge additions & removals.  |
| `regen <graphson> <target-dir>` | *(Stub)* Walk graph and scaffold code/tests.           |

All commands accept `-v` for chatty logs and `--help` for options.

## Tech stack

* **networkx** – in-memory property graph
* **jsonschema** – node shape validation
* **uv** – dev-env + script runner
* **uuid / hashlib** – deterministic IDs & checksums
* *(Coming soon)* **LangGraph + GPT-4o** – agentic patch proposals

## Samples

`./samples/sql/schema.sql` and `./samples/stories/login.md` are tiny but real.
Add more artefacts and rerun `build`—Gary merges them by stable UUID so diffs stay sane.

## Contributing

Gary welcomes snail-pace or lightning-fast pull requests alike.
Open an issue, fork, fix, and let the slime trails converge.

## License

MIT – do what you want, just feed the snail.

---

Created by **Iwan van der Kleijn**, 2025.
*SpongeBob’s Gary was resilient; may this Gary be refactor-proof.*
