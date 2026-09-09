"""Optional PDF extraction. Importing this module has no runtime dependency."""
VERSION = "pymupdf-pages-1"


def normalize(data, path, sha256):
    base = {"kind": "source", "path": path, "sha256": sha256, "source_identity": path,
            "format": "pdf", "extractor": VERSION, "segments": [], "limitations": []}
    try:
        import pymupdf
    except ImportError:
        base["limitations"] = ["PDF extraction unavailable; install the separately declared extraction dependency through an authorized operation. Read the original PDF directly."]
        base["extraction_status"] = "unavailable"
        return base
    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            base["metadata"] = doc.metadata or {}
            base["page_count"] = len(doc)
            if doc.needs_pass:
                base["extraction_status"] = "unsupported"
                base["limitations"].append("Encrypted PDF requires an authorized unlocked source.")
                return base
            for n, page in enumerate(doc, start=1):
                text = page.get_text("text", sort=False)
                base["segments"].append({"text": text, "page": n,
                                         "locator": f"{path}#page={n}", "heading": f"Page {n}"})
                if not text.strip():
                    base["limitations"].append(f"Page {n}: no extractable text; scan/OCR or visual inspection required.")
            base["extraction_status"] = "extracted" if any(x["text"].strip() for x in base["segments"]) else "unsupported"
    except (RuntimeError, ValueError) as error:
        base["extraction_status"] = "unsupported"
        base["limitations"].append(f"PDF extraction failed ({type(error).__name__}); inspect the original source.")
    base["limitations"].append("PDF text order, equations, tables and complex layouts require visual confirmation; extracted text is source evidence, not an accepted finding.")
    return base
