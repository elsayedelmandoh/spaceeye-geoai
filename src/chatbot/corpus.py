"""Load the approved document corpus and split Markdown into retrievable passages."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DOCUMENT_PATHS = (
    "docs/requirements/01-specs.md",
    "docs/requirements/ACUD-Rubric.md",
    "data/DATASET_CONTRACT.md",
    "data/BACKTEST_CURRENT.md",
    "data/EW_REPORT_CURRENT.md",
    "data/SCENARIO_CONTRACT_CURRENT.md",
    "docs/deliverables/method-card.md",
    "docs/deliverables/INSPECTION_DOSSIERS.md",
    "docs/deliverables/user-guide.md",
    "docs/deliverables/decision-memo.md",
    "docs/deliverables/responsible-ai.md",
    "docs/deliverables/kpi-cards.md",
    "docs/deliverables/data-request.md",
    "docs/deliverables/technical-track-a.md",
)
EXTERNAL_KNOWLEDGE_DIR = REPO_ROOT / "data" / "knowledge" / "external"

_LOGGER = logging.getLogger(__name__)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
_PERSONAL_VALUE_RE = re.compile(
    r"(?i)\b(reviewer|developer|owner|author|compound)(\s*:\s*\**\s*)([^*\n]+)"
)
_CODE_VALUE_RE = re.compile(r"^[CD]\d{2,3}$")


@dataclass(frozen=True)
class _Section:
    """One heading and its Markdown body."""

    heading: str
    heading_line: str
    body: str


@dataclass(frozen=True)
class Passage:
    """A retrievable document fragment with source provenance."""

    path: str
    heading: str
    text: str
    title: str | None = None
    source_url: str | None = None
    retrieved: str | None = None

    @property
    def word_count(self) -> int:
        """Return the whitespace-delimited word count used for chunk sizing."""

        return len(self.text.split())

    @property
    def citation(self) -> str:
        """Return the dashboard citation format required by the chatbot."""

        return f"{self.path} · {self.heading or 'Overview'}"


def _parse_front_matter(text: str, path: str) -> dict[str, Any]:
    """Parse optional YAML front matter without letting malformed metadata stop loading."""

    match = _FRONT_MATTER_RE.match(text)
    if match is None:
        return {}
    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        _LOGGER.warning("Ignoring malformed front matter in %s", path)
        return {}
    if not isinstance(metadata, dict):
        _LOGGER.warning("Ignoring non-mapping front matter in %s", path)
        return {}
    return metadata


def _strip_front_matter(text: str) -> str:
    """Remove a leading YAML front-matter block from document text."""

    return _FRONT_MATTER_RE.sub("", text, count=1)


def _redact_personal_values(text: str) -> str:
    """Redact labeled personal values while preserving compound or developer codes."""

    def replace_value(match: re.Match[str]) -> str:
        if _CODE_VALUE_RE.fullmatch(match.group(3).strip()):
            return match.group(0)
        return f"{match.group(1)}{match.group(2)}[redacted]"

    return _PERSONAL_VALUE_RE.sub(replace_value, text)


def _is_fence_start(line: str) -> bool:
    """Return whether a line opens or closes a Markdown code fence."""

    stripped = line.strip()
    return stripped.startswith(("```", "~~~"))


def _markdown_blocks(text: str) -> list[str]:
    """Split text into paragraph-like blocks while preserving fenced code blocks."""

    blocks: list[str] = []
    current: list[str] = []
    in_fence = False

    for line in text.splitlines():
        if _is_fence_start(line):
            in_fence = not in_fence
            current.append(line)
            continue
        if not in_fence and not line.strip():
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line)

    if current:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block]


def _split_oversized_block(block: str, max_words: int) -> list[str]:
    """Split one oversized paragraph at word boundaries."""

    words = block.split()
    return [" ".join(words[start : start + max_words]) for start in range(0, len(words), max_words)]


def _flush_block_group(
    current: list[str],
    grouped: list[str],
) -> tuple[list[str], int]:
    """Flush one accumulated paragraph group and reset its word count."""

    if current:
        grouped.append("\n\n".join(current))
    return [], 0


def _group_blocks(blocks: list[str], min_words: int, max_words: int) -> list[str]:
    """Group Markdown blocks into passages near the requested word range."""

    grouped: list[str] = []
    current: list[str] = []
    current_words = 0
    for block in blocks:
        block_words = len(block.split())
        if block_words > max_words:
            current, current_words = _flush_block_group(current, grouped)
            grouped.extend(_split_oversized_block(block, max_words))
            continue
        reached_target = current_words >= min_words
        would_overflow = current_words + block_words > max_words
        if current and (reached_target or would_overflow):
            current, current_words = _flush_block_group(current, grouped)
        current.append(block)
        current_words += block_words
    if current:
        grouped.append("\n\n".join(current))
    return grouped


def _markdown_sections(body: str) -> list[_Section]:
    """Parse Markdown into heading-delimited sections."""

    sections: list[_Section] = []
    heading = "Overview"
    heading_line = ""
    section_lines: list[str] = []
    in_fence = False
    for line in body.splitlines():
        if _is_fence_start(line):
            in_fence = not in_fence
        heading_match = None if in_fence else _HEADING_RE.match(line)
        if heading_match is None:
            section_lines.append(line)
            continue
        sections.append(_Section(heading, heading_line, "\n".join(section_lines)))
        heading = heading_match.group(2).strip()
        heading_line = line.strip()
        section_lines = []
    sections.append(_Section(heading, heading_line, "\n".join(section_lines)))
    return sections


def _section_passages(
    path: str,
    section: _Section,
    min_words: int,
    max_words: int,
) -> list[Passage]:
    """Split one heading section into passages."""

    blocks = _markdown_blocks(section.body)
    grouped_texts = _group_blocks(blocks, min_words, max_words)
    prefix = f"{section.heading_line}\n\n" if section.heading_line else ""
    return [
        Passage(
            path=path,
            heading=section.heading,
            text=f"{prefix}{grouped_text}".strip(),
        )
        for grouped_text in grouped_texts
    ]


def split_markdown(
    path: str,
    text: str,
    min_words: int = 120,
    max_words: int = 200,
) -> list[Passage]:
    """Split Markdown on headings and paragraphs while retaining heading context."""

    if min_words < 1 or max_words < min_words:
        raise ValueError("Passage word limits must satisfy 1 <= min_words <= max_words")
    body = _redact_personal_values(_strip_front_matter(text))
    return [
        passage
        for section in _markdown_sections(body)
        for passage in _section_passages(path, section, min_words, max_words)
    ]


def _read_text(path: Path, display_path: str) -> str | None:
    """Read one UTF-8 document, logging and skipping unreadable files."""

    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _LOGGER.warning(
            "Skipping unreadable document %s (%s)",
            display_path,
            type(exc).__name__,
        )
        return None


def _first_heading(text: str) -> str | None:
    """Return the first Markdown heading without reading external metadata."""

    for line in _strip_front_matter(text).splitlines():
        match = _HEADING_RE.match(line)
        if match is not None:
            return _redact_personal_values(match.group(2).strip())
    return None


def _external_document_paths(external_dir: Path) -> list[Path]:
    """Return every external Markdown file in stable order."""

    if not external_dir.is_dir():
        _LOGGER.warning("External knowledge directory is missing: %s", external_dir)
        return []
    return sorted(external_dir.rglob("*.md"))


def _relative_display_path(path: Path, repo_root: Path) -> str:
    """Return a stable repository-relative path when possible."""

    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_project_passages(
    repo_root: Path,
    project_paths: tuple[str, ...],
) -> list[Passage]:
    """Load the fixed project-document list."""

    passages: list[Passage] = []
    for relative_path in project_paths:
        path = repo_root / relative_path
        if not path.is_file():
            _LOGGER.warning("Skipping missing fixed document: %s", relative_path)
            continue
        text = _read_text(path, relative_path)
        if text is None:
            continue
        title = _first_heading(text)
        passages.extend(
            replace(passage, title=title)
            for passage in split_markdown(relative_path, text)
        )
    return passages


def _external_metadata(text: str, display_path: str, path: Path) -> dict[str, str]:
    """Read and validate external-source front matter."""

    metadata = _parse_front_matter(text, display_path)
    if not metadata:
        _LOGGER.warning("External document is missing front matter: %s", display_path)
    for field in ("title", "source_url", "retrieval_date"):
        if not str(metadata.get(field) or "").strip():
            _LOGGER.warning(
                "External document %s is missing front-matter field %s",
                display_path,
                field,
            )
    return {
        "title": _redact_personal_values(str(metadata.get("title") or path.stem)),
        "source_url": str(metadata.get("source_url") or ""),
        "retrieved": str(metadata.get("retrieval_date") or ""),
    }


def _load_external_passages(repo_root: Path, external_dir: Path) -> list[Passage]:
    """Load every external Markdown source with its provenance metadata."""

    passages: list[Passage] = []
    for path in _external_document_paths(external_dir):
        display_path = _relative_display_path(path, repo_root)
        text = _read_text(path, display_path)
        if text is None:
            continue
        metadata = _external_metadata(text, display_path, path)
        passages.extend(
            replace(passage, **metadata)
            for passage in split_markdown(display_path, text)
        )
    return passages


def load_corpus(
    repo_root: Path = REPO_ROOT,
    project_paths: tuple[str, ...] = PROJECT_DOCUMENT_PATHS,
    external_dir: Path = EXTERNAL_KNOWLEDGE_DIR,
) -> list[Passage]:
    """Load fixed project documents and every external Markdown source."""

    return [
        *_load_project_passages(repo_root, project_paths),
        *_load_external_passages(repo_root, external_dir),
    ]
