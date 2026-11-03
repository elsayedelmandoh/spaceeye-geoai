
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from chatbot.app.core.config import REPO_ROOT


CONTEXTS_DIR = (
    REPO_ROOT
    / "artifacts"
    / "ready_data_v7"
    / "SpaceEye_R7_READY_DATA_2026-10-31_v7"
    / "inspection"
    / "inspection_contexts"
)


def _json_key(item: dict) -> str:
    return json.dumps(
        item,
        sort_keys=True,
        ensure_ascii=False,
    )


def _make_chunk(
    chunk_id: str,
    document: str,
    metadata: dict,
) -> dict:
    return {
        "id": chunk_id,
        "document": document.strip(),
        "metadata": metadata,
    }


def build_documents() -> list[dict]:
    if not CONTEXTS_DIR.exists():
        raise FileNotFoundError(
            f"Inspection contexts not found: {CONTEXTS_DIR}"
        )

    statements = {}
    rules = {}
    complaints = {}
    visits = {}

    sources = {}

    for path in sorted(CONTEXTS_DIR.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))

        code = data.get("code")
        quarter = data.get("quarter")

        public = data.get("public_evidence", {})
        generated = data.get("generated_operations", {})

        # Collect source references
        for source in public.get("sources", []):
            statement_id = source.get("statement_id")
            if statement_id:
                sources[statement_id] = source

        # Collect published statements
        for item in public.get("statements", []):
            key = item.get("statement_id")
            if not key:
                continue

            if key not in statements:
                statements[key] = {
                    "item": item,
                    "versions": set(),
                    "compounds": set(),
                    "quarters": set(),
                }

            record = statements[key]
            record["versions"].add(_json_key(item))
            record["compounds"].add(code)
            record["quarters"].add(quarter)

        # Collect rule summaries
        for item in public.get("rules", []):
            key = item.get("rule_id")
            if not key:
                continue

            if key not in rules:
                rules[key] = {
                    "item": item,
                    "versions": set(),
                }

            rules[key]["versions"].add(_json_key(item))

        # Collect synthetic complaint texts
        for item in generated.get("latest_masked_texts", []):
            key = item.get("complaint_id")

            if not key:
                continue

            if key not in complaints:
                complaints[key] = {
                    "item": item,
                    "versions": set(),
                    "compounds": set(),
                    "quarters": set(),
                }

            record = complaints[key]
            record["versions"].add(_json_key(item))
            record["compounds"].add(code)
            record["quarters"].add(quarter)

        # Collect synthetic inspection visits
        for item in generated.get("synthetic_visits", []):
            key = item.get("visit_id")

            if not key:
                continue

            if key not in visits:
                visits[key] = {
                    "item": item,
                    "versions": set(),
                    "compounds": set(),
                    "quarters": set(),
                }

            record = visits[key]
            record["versions"].add(_json_key(item))
            record["compounds"].add(code)
            record["quarters"].add(quarter)

    chunks = []

    # 1. Published statements
    for statement_id, record in statements.items():
        if len(record["versions"]) != 1:
            raise ValueError(
                f"Conflicting statement versions: {statement_id}"
            )

        item = record["item"]
        source = sources.get(statement_id, {})

        parts = [
            f"Published statement: {statement_id}",
            f"Compound: {item.get('code', 'Unknown')}",
            f"Type: {item.get('kind', '')}",
            f"Subtype: {item.get('subtype', '')}",
            f"Detail: {item.get('detail') or 'Not provided'}",
            f"Value: {item.get('value')}",
            f"Qualifier: {item.get('qualifier', '')}",
            f"Published date: {item.get('published_date', '')}",
            f"Period: {item.get('period_start')} to {item.get('period_end')}",
            f"Record ID: {item.get('record_id', '')}",
            f"Verdict: {item.get('verdict', '')}",
            f"Origin: {item.get('origin', 'unknown')}",
            f"Source URL: {source.get('url', 'Not available')}",
        ]

        metadata = {
            "document_type": "published_statement",
            "statement_id": statement_id,
            "origin": item.get("origin", "unknown"),
            "compound": item.get("code", "unknown"),
            "available_in_contexts": ",".join(
                sorted(record["quarters"])
            ),
            "published_date": item.get("published_date") or "",
            "record_id": item.get("record_id") or "",
            "source_url": source.get("url") or "",
        }

        chunks.append(
            _make_chunk(
                f"statement:{statement_id}",
                "\n".join(parts),
                metadata,
            )
        )

    # 2. Rule summaries
    for rule_id, record in rules.items():
        if len(record["versions"]) != 1:
            raise ValueError(
                f"Conflicting rule versions: {rule_id}"
            )

        item = record["item"]

        parts = [
            f"Rule summary: {rule_id}",
            f"Source: {item.get('source', '')}",
            f"Article: {item.get('article', '')}",
            f"Rule: {item.get('rule', '')}",
            f"Value: {item.get('value')}",
            f"Unit: {item.get('unit', '')}",
            f"Origin: {item.get('origin', 'unknown')}",
            "Important: This is a summarized rule, not the original legal text.",
        ]

        metadata = {
            "document_type": "rule_summary",
            "rule_id": rule_id,
            "origin": item.get("origin", "unknown"),
            "source": item.get("source") or "",
            "article": item.get("article") or "",
        }

        chunks.append(
            _make_chunk(
                f"rule:{rule_id}",
                "\n".join(parts),
                metadata,
            )
        )

    # 3. Synthetic complaint texts
    for complaint_id, record in complaints.items():
        if len(record["versions"]) != 1:
            raise ValueError(
                f"Conflicting complaint versions: {complaint_id}"
            )

        item = record["item"]
        text_ar = item.get("text_ar")

        if not isinstance(text_ar, str) or not text_ar.strip():
            continue

        parts = [
            f"Synthetic complaint: {complaint_id}",
            f"Compound: {item.get('code', '')}",
            f"Date: {item.get('created_at', '')}",
            f"Channel: {item.get('channel', '')}",
            f"Category: {item.get('category', '')}",
            f"Complaint text: {text_ar.strip()}",
            "Data origin: Synthetic - for training only.",
            "This is not an actual customer complaint.",
        ]

        metadata = {
            "document_type": "synthetic_complaint",
            "complaint_id": complaint_id,
            "origin": "synthetic",
            "synthetic": True,
            "compound": item.get("code") or "unknown",
            "category": item.get("category") or "",
            "available_in_contexts": ",".join(
                sorted(record["quarters"])
            ),
        }

        chunks.append(
            _make_chunk(
                f"complaint:{complaint_id}",
                "\n".join(parts),
                metadata,
            )
        )

    # 4. Synthetic inspection visits
    for visit_id, record in visits.items():
        if len(record["versions"]) != 1:
            raise ValueError(
                f"Conflicting visit versions: {visit_id}"
            )

        item = record["item"]
        note = item.get("note")

        if not isinstance(note, str) or not note.strip():
            continue

        parts = [
            f"Synthetic inspection exercise: {visit_id}",
            f"Compound: {item.get('code', '')}",
            f"Source quarter: {item.get('source_quarter', '')}",
            f"Visit date: {item.get('visit_date', '')}",
            f"Result: {item.get('result', '')}",
            f"Note: {note.strip()}",
            f"State basis: {item.get('state_basis', '')}",
            "Data origin: Synthetic - for training only.",
            "This is not a real field inspection.",
        ]

        metadata = {
            "document_type": "synthetic_visit",
            "visit_id": visit_id,
            "origin": "synthetic",
            "synthetic": True,
            "compound": item.get("code") or "unknown",
            "source_quarter": item.get("source_quarter") or "",
            "available_in_contexts": ",".join(
                sorted(record["quarters"])
            ),
            "result": item.get("result") or "",
        }

        chunks.append(
            _make_chunk(
                f"visit:{visit_id}",
                "\n".join(parts),
                metadata,
            )
        )

    return chunks


def preview_ingestion() -> dict:
    chunks = build_documents()

    counts = {}

    for chunk in chunks:
        document_type = chunk["metadata"]["document_type"]
        counts[document_type] = counts.get(document_type, 0) + 1

    return {
        "total_chunks": len(chunks),
        "counts": counts,
        "unique_ids": len({chunk["id"] for chunk in chunks}),
        "duplicate_ids": len(chunks) - len({chunk["id"] for chunk in chunks}),
        "chunks": chunks,
    }
