SYSTEM
You are an experienced software engineer.

## Goal
Upgrade the existing **Gary** project so that artefact ingestion supports **two complementary paths**:

1. **Deterministic parsers** (already present)  
   * SQL DDL  → `Table` / `Column` nodes  
   * Markdown User Stories → `Story` nodes 
   * Generic Markdown documents (i.e. "documenation)

   Create types in the json graph schema which supports these types
   Document these types in the doc directory (format for documentation: GIthub documentation. Be sufficiently verbose to document the schemas well) 

   Use the document.md in samples/markdown for the markdown test case.

2. **LLM-based importer** for any artefact that lacks a cheap parser.  
   * Uses OpenAI function-calling (JSON mode) to return validated MetaGraph nodes.  
   * Falls back to deterministic path if artefact extension is recognised AND file ≤ 16 KB.
   * Add a type specifier to the genetic type so the user/llm can determine what the original type has been
   * Create an adecuate test. Use the samples, widget.xml as a test case

## High-level architecture
```

gary/
├─ cli.py               # extend with `import`, `apply`
├─ metagraph/
│   ├─ ...
│   ├─ ai\..            # all AI/Langchain related funcionality here
│   ├─ importer\llm.py  # **new** – universal LLM importer
│   ├─ importer\core.py # **new** – orchestrates parser selection
│   ├─ patch\io.py      # **new** – read/write RFC-6902 patches
│   └─ validation.py    # edge-type + JSON-Schema helpers
├─ regen.py

Add the proper __init__.py module specifiers.

Add the markdown deterministic parser compatible with the above document structure.

```

## Mandatory constraints
1. **Language**: Python 3.12; only stdlib + `networkx`, `jsonschema`, `jsonpatch`, `openai`.
2. **MetaGraph node schema** unchanged.
3. **LLM call contract**  
   * Model: env var `OPENAI_MODEL` (default `gpt-4.1`).  
   * System prompt:  
     ```
     You are MetaGraph-ImporterGPT. Return ONLY JSON conforming to:
     {"nodes":[Node…],"errors":[string…]}
     ```  
   * Function name `emit_nodes`, parameters = envelope described above.
   * If first response fails JSON-Schema validation, send a *repair* prompt once.
4. **Importer decision logic**  
   ```python
   def choose_importer(path: Path) -> Literal["deterministic","llm"]:
       if path.suffix in {".sql",".md"} and path.stat().st_size <= 16_384:
           return "deterministic"
       return "llm"
    ```

5. **CLI additions**

   ```
   gary import <file>...          # auto-chooser; outputs patch.json
   gary apply  <patch.json>       # merges into current graphson
   ```

   * `import` pipes to stdout unless `-o` is given.
   * `apply` validates graph after merge; rejects patch if invalid.
6. **Caching**

   * SHA-256 of artefact → `.cache/import/{hash}.json`.
   * Re-use cached patch when artefact unchanged.

## Sample additions

Add `samples/xml/widget.xml` (random DSL) to prove LLM path.

## AI Implementation

Use Langchain with OpenAI for the AI implementation. Use async implementation. If this requires a global change, do so. Use python-dotenv to get the OPENAI_API_KEY from the .env file


## Tests

* `tests/test_import_llm.py` – monkeypatch `openai` with stub returning fixture JSON.
* `tests/test_apply_patch.py` – ensure graph node count increases after patch.

## README changes

* New “Importing artefacts” section describing `gary import` / `apply` and dual strategy.
* Add env vars `OPENAI_MODEL` and `OPENAI_API_KEY`.

## Deliverables

Return code files exactly matching repo layout.
Update existing files in-place; mark new content with `# --- v0.3 ADDITION ---` comments for clarity.

Return only code blocks—no extra prose.


