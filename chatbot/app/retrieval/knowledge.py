"""Chunk the sourced knowledge documents (chatbot/knowledge/external/*.md)."""

import re
from pathlib import Path

import yaml

from chatbot.app.core.config import CHATBOT_DIR, REPO_ROOT

KNOWLEDGE_DIR = CHATBOT_DIR / "knowledge" / "external"
DOCUMENT_TYPE = "external_knowledge"

_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def _split_front_matter(text: str) -> tuple[dict, str]:
    match = _FRONT_MATTER.match(text)
    if not match:
        return {}, text
    meta = yaml.safe_load(match.group(1))
    return (meta if isinstance(meta, dict) else {}), text[match.end():]


def _split_sections(body: str) -> list[tuple[str, str]]:
    """Return (heading, text) pairs; text before the first heading has an empty heading."""
    sections: list[tuple[str, list[str]]] = [("", [])]
    in_fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        heading = None if in_fence else _HEADING.match(line)
        if heading:
            sections.append((heading.group(2), []))
        else:
            sections[-1][1].append(line)
    return [(h, "\n".join(lines).strip()) for h, lines in sections]


def build_knowledge_chunks(knowledge_dir: Path = KNOWLEDGE_DIR) -> list[dict]:
    """One chunk per non-empty markdown section, carrying source metadata for citations."""
    chunks = []
    for path in sorted(knowledge_dir.rglob("*.md")):
        meta, body = _split_front_matter(path.read_text(encoding="utf-8"))
        try:
            rel_path = path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel_path = path.as_posix()
        title = str(meta.get("title") or path.stem)

        for index, (heading, text) in enumerate(_split_sections(body)):
            if not text:
                continue
            parts = [f"Source document: {title}"]
            if heading:
                parts.append(f"Section: {heading}")
            parts.append(text)
            chunks.append({
                "id": f"knowledge:{path.stem}:{index}",
                "document": "\n".join(parts),
                "metadata": {
                    "document_type": DOCUMENT_TYPE,
                    "origin": "external_source",
                    "title": title,
                    "section": heading,
                    "source_url": str(meta.get("source_url") or ""),
                    "retrieval_date": str(meta.get("retrieval_date") or ""),
                    "kind": str(meta.get("kind") or ""),
                    "language": str(meta.get("language") or ""),
                    "file_path": rel_path,
                },
            })
    return chunks
