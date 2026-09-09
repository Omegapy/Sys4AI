"""Literal TeX extraction; mathematical expressions are never rewritten."""
import re

VERSION = "tex-literal-1"
SECTION = re.compile(r"\\(?P<kind>part|chapter|section|subsection|subsubsection|paragraph)\*?(?:\[[^\]]*\])?\{(?P<title>[^{}]*(?:\{[^{}]*\}[^{}]*)*)\}")


def normalize(text, path, sha256):
    matches = list(SECTION.finditer(text))
    starts = [(0, "Preamble")]
    starts.extend((m.start(), m.group("title")) for m in matches if m.start())
    if matches and matches[0].start() == 0:
        starts[0] = (0, matches[0].group("title"))
    segments = []
    for i, (start, heading) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        raw = text[start:end]
        if not raw.strip():
            continue
        labels = re.findall(r"\\label\{([^}]+)\}", raw)
        refs = re.findall(r"\\(?:eqref|ref|pageref|autoref|cref|Cref)\{([^}]+)\}", raw)
        keys = re.findall(r"\\(?:cite\w*|bibitem)(?:\[[^\]]*\])*\{([^}]+)\}", raw)
        envs = re.findall(r"\\begin\{([^}]+)\}", raw)
        line = text.count("\n", 0, start) + 1
        segments.append({"text": raw, "locator": f"{path}:{line}", "heading": heading,
                         "line": line, "labels": labels, "references": refs,
                         "bibliography_keys": keys, "environments": envs})
    return {"kind": "source", "path": path, "sha256": sha256, "source_identity": path,
            "format": "tex", "extractor": VERSION, "segments": segments,
            "limitations": ["Literal source extraction; macros and included files are not expanded or compiled."]}
