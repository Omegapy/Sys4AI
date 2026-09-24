"""Regenerate the static, dependency-free client schema and types from frozen v1.

Run with the depot Python 3.12. Runtime mechanics are in contracts-runtime.ts.in.
Neither the browser nor this generator resolves remote schema references.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCHEMA = ROOT / "ONTOLOGY-depo/schema/explorer-v1.json"
EXPECTED = "f494fde5dfb796a3dfd88db40d20487d965ce57d15b87d82117651dd5c8766ee"
raw = SCHEMA.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
schema = json.loads(raw)


def literal(v):
    if isinstance(v, list):
        return "[" + ", ".join(literal(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + "; ".join(json.dumps(k) + ": " + literal(x) for k, x in v.items()) + " }"
    return json.dumps(v, ensure_ascii=False)


def ts(s):
    bits = []
    if "$ref" in s:
        bits.append(s["$ref"].split("/")[-1])
    if "const" in s:
        bits.append(literal(s["const"]))
    if "enum" in s:
        bits.append("(" + " | ".join(literal(x) for x in s["enum"]) + ")")
    if "properties" in s:
        req = set(s.get("required", []))
        bits.append("{ " + "; ".join(json.dumps(k) + ("" if k in req else "?") + ": " + ts(v) for k, v in s["properties"].items()) + " }")
    elif "type" in s:
        t = s["type"]
        bits.append({"integer": "number", "number": "number", "string": "string", "boolean": "boolean", "null": "null", "object": "{ [key: string]: CanonicalJson }", "array": "Array<" + ts(s.get("items", {})) + ">"}.get(t, "unknown"))
    for u in ["oneOf", "anyOf"]:
        if u in s:
            bits.append("(" + " | ".join(ts(v) for v in s[u]) + ")")
    if "allOf" in s:
        bits.extend(ts(v) for v in s["allOf"] if "if" not in v)
    return " & ".join(bits) if bits else "unknown"


def clean(v):
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items() if k not in ["description", "default", "x-http-method", "x-http-path", "x-http-status"]}
    return [clean(x) for x in v] if isinstance(v, list) else v


lines = ["// Generated definitions: tests/client-foundations/generate_contracts.py.",
         "// Semantic validation below is required in addition to schema validation.",
         f'export const CONTRACT_SCHEMA_SHA256 = "{EXPECTED}";',
         "export type CanonicalJson = null | boolean | number | string | CanonicalJson[] | { [key: string]: CanonicalJson };"]
lines.extend(f"export type {k} = {ts(v)};" for k, v in schema["$defs"].items() if k != "CanonicalJson")
lines.append("export interface WireTypes { " + "; ".join(k + ": " + k for k in schema["$defs"]) + " }")
lines.append("const DEFINITIONS: Record<string, Schema> = " + json.dumps(clean(schema["$defs"]), ensure_ascii=False, separators=(",", ":")) + ";")
# Match Python's canonical casefold/split exactly, including sharp S, final sigma,
# and Python whitespace that differs from JavaScript trim. This is a static table,
# not a new normalization or a browser-dependent Unicode lowercasing rule.
fold = {chr(i): chr(i).casefold() for i in range(0x110000) if chr(i).casefold() != chr(i)}
lines.append("const CASEFOLD: Record<string, string> = " + json.dumps(fold, ensure_ascii=True, separators=(",", ":")) + ";")
lines.append("const WHITESPACE = new Set(" + json.dumps([i for i in range(0x110000) if chr(i).isspace()]) + ");")
lines.append(Path(__file__).with_name("contracts-runtime.ts.in").read_text())
out = Path(__file__).parents[2] / "src/contracts.ts"
out.write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({"path": str(out.relative_to(ROOT)), "sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "bytes": out.stat().st_size}))
