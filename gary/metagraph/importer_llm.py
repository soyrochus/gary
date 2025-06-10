"""LLM-based artefact importer using OpenAI."""

# --- v0.3 ADDITION ---
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from jsonschema import validate
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser

NODE_ENVELOPE_SCHEMA = {
    "type": "object",
    "properties": {
        "nodes": {"type": "array", "items": {"type": "object"}},
        "errors": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["nodes", "errors"],
}

SYSTEM_PROMPT = (
    'You are MetaGraph-ImporterGPT. Return ONLY JSON conforming to:'
    ' {"nodes":[Node…],"errors":[string…]}'
)


async def import_with_llm(path: Path) -> list[dict]:
    """Import artefact using OpenAI function calling."""
    load_dotenv()
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{text}"),
    ])
    chain = prompt | llm.bind_functions(
        [
            {
                "name": "emit_nodes",
                "parameters": NODE_ENVELOPE_SCHEMA,
            }
        ],
        function_call={"name": "emit_nodes"},
    ) | JsonOutputFunctionsParser()
    text = path.read_text()
    result = await chain.ainvoke({"text": text})
    try:
        validate(instance=result, schema=NODE_ENVELOPE_SCHEMA)
    except Exception:
        repair = await chain.ainvoke({"text": text + "\nRepair."})
        result = repair
    return result.get("nodes", [])
