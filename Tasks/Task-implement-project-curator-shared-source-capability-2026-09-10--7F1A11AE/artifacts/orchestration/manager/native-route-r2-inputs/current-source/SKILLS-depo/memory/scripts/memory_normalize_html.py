"""Extract local HTML content without executing it or fetching resources."""
from html.parser import HTMLParser
import re

VERSION = "html-text-1"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
EXCLUDED = {"head", "nav", "footer", "aside", "form", "script", "style", "template", "svg", "noscript"}


class ContentParser(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.stack = []
        self.parts = []
        self.segments = []
        self.heading = "Document"
        self.anchor = None
        self.line = 1
        self.in_heading = False
        self.heading_parts = []

    def flush(self):
        text = re.sub(r"[ \t]+", " ", "".join(self.parts)).strip()
        if text:
            self.segments.append({"text": text, "heading": self.heading,
                                  "locator": f"{self.path}#{self.anchor}" if self.anchor else f"{self.path}:{self.line}",
                                  "line": self.line})
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        blocked = (bool(self.stack and self.stack[-1][1]) or tag in EXCLUDED
                   or "hidden" in attr or attr.get("aria-hidden") == "true"
                   or attr.get("role") in {"navigation", "banner", "complementary"})
        if tag not in VOID:
            self.stack.append((tag, blocked))
        if blocked:
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.flush()
            self.in_heading = True
            self.heading_parts = []
            self.anchor = attr.get("id")
            self.line = self.getpos()[0]
        elif tag in {"p", "div", "li", "br", "tr", "article", "section", "pre"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        blocked = bool(self.stack and self.stack[-1][1])
        if not blocked:
            if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self.in_heading:
                self.heading = "".join(self.heading_parts).strip() or "Untitled section"
                self.parts.append(self.heading + "\n")
                self.in_heading = False
            elif tag in {"p", "div", "li", "tr", "pre"}:
                self.parts.append("\n")
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.stack and self.stack[-1][1]:
            return
        if self.in_heading:
            self.heading_parts.append(data)
        else:
            self.parts.append(data)


def normalize(text, path, sha256):
    parser = ContentParser(path)
    parser.feed(text)
    parser.close()
    parser.flush()
    return {"kind": "source", "path": path, "sha256": sha256, "source_identity": path,
            "format": "html", "extractor": VERSION, "segments": parser.segments,
            "limitations": ["Local static HTML text; scripts, remote resources and interactive content are not evaluated."]}
