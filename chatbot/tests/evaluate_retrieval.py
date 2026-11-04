
from collections import Counter
import json
from pathlib import Path

from chatbot.app.retrieval.pipeline import retrieve_context


TEST_CASES = [
    {
        "name": "Project information C18",
        "query": "project details C18",
        "expected_type": None,
        "expected_compound": "C18",
    },
    {
        "name": "Published delivery statements C18",
        "query": "delivery date C18",
        "expected_type": "published_statement",
        "expected_compound": "C18",
    },
    {
        "name": "Delivery delay rules",
        "query": "rules about delivery delay",
        "expected_type": "rule_summary",
        "expected_compound": None,
    },
    {
        "name": "Complaints C18",
        "query": "complaints C18",
        "expected_type": "synthetic_complaint",
        "expected_compound": "C18",
    },
    {
        "name": "Inspection visits C18",
        "query": "inspection visits C18",
        "expected_type": "synthetic_visit",
        "expected_compound": "C18",
    },
]


def evaluate_case(case: dict) -> dict:
    result = retrieve_context(
        query=case["query"],
        n_results=5,
    )

    evidence = result.get("results", [])
    metadata_list = [
        item.get("metadata") or {}
        for item in evidence
    ]

    ids = [item.get("id") for item in evidence]

    actual_types = Counter(
        metadata.get("document_type")
        for metadata in metadata_list
    )

    actual_compounds = [
        metadata.get("compound_code")
        or metadata.get("compound")
        for metadata in metadata_list
    ]

    # Check document type
    if case["expected_type"] is None:
        type_check = "N/A"
    else:
        type_check = (
            "PASS"
            if evidence and all(
                metadata.get("document_type") == case["expected_type"]
                for metadata in metadata_list
            )
            else "FAIL"
        )

    # Check compound association
    if case["expected_compound"] is None:
        compound_check = "N/A"
    else:
        matching = [
            code for code in actual_compounds
            if code == case["expected_compound"]
        ]

        compound_check = (
            "PASS"
            if evidence and len(matching) == len(evidence)
            else "FAIL"
        )

    # Check duplicate IDs
    duplicate_check = (
        "PASS" if len(ids) == len(set(ids)) else "FAIL"
    )

    # Check distance values
    distances = [
        item.get("distance")
        for item in evidence
        if isinstance(item.get("distance"), (int, float))
    ]

    distance_check = (
        "PASS"
        if len(distances) == len(evidence)
        else "CHECK"
    )

    return {
        "name": case["name"],
        "query": case["query"],
        "intent": result.get("intent"),
        "evidence_count": len(evidence),
        "document_types": dict(actual_types),
        "type_check": type_check,
        "compound_check": compound_check,
        "duplicate_check": duplicate_check,
        "distance_check": distance_check,
        "distances": distances,
        "evidence": [
            {
                "id": item.get("id"),
                "type": (item.get("metadata") or {}).get("document_type"),
                "compound": (
                    (item.get("metadata") or {}).get("compound_code")
                    or (item.get("metadata") or {}).get("compound")
                ),
                "origin": (item.get("metadata") or {}).get("origin"),
                "distance": item.get("distance"),
            }
            for item in evidence
        ],
    }


def main():
    results = []

    print("=" * 65)
    print("SPACE EYE - RETRIEVAL QUALITY EVALUATION")
    print("=" * 65)

    for index, case in enumerate(TEST_CASES, start=1):
        print(f"\n[{index}/{len(TEST_CASES)}] {case['name']}")
        print(f"Question: {case['query']}")

        try:
            result = evaluate_case(case)
            results.append(result)

            print(f"Intent: {result['intent']}")
            print(f"Evidence: {result['evidence_count']}")
            print(f"Document types: {result['document_types']}")
            print(f"Type check: {result['type_check']}")
            print(f"Compound check: {result['compound_check']}")
            print(f"Duplicate check: {result['duplicate_check']}")
            print(f"Distance check: {result['distance_check']}")

            for item in result["evidence"]:
                print(
                    f"  - {item['id']} | "
                    f"{item['type']} | "
                    f"{item['compound']} | "
                    f"distance={item['distance']}"
                )

        except Exception as exc:
            print(f"ERROR: {exc}")
            results.append({
                "name": case["name"],
                "error": str(exc),
            })

    report_path = (
        Path(__file__).resolve().parents[1]
        / "retrieval_evaluation_results.json"
    )

    report_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 65)
    print("EVALUATION SUMMARY")
    print("=" * 65)
    print(f"Total cases: {len(results)}")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
