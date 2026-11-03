
import json
import sys
from datetime import datetime
from pathlib import Path

from chatbot.app.generation.service import answer_question


sys.stdout.reconfigure(encoding="utf-8")

TEST_CASES = [
    {
        "name": "Project information",
        "question": "project details C18",
        "expected_intent": "project_info",
    },
    {
        "name": "Latest KPI",
        "question": "latest KPI for C18",
        "expected_intent": "project_info",
    },
    {
        "name": "Published statements",
        "question": "delivery date C18",
        "expected_intent": "published_statements",
    },
    {
        "name": "Rules",
        "question": "rules about delivery delay",
        "expected_intent": "rules",
    },
    {
        "name": "Complaints",
        "question": "complaints C18",
        "expected_intent": "complaints",
    },
    {
        "name": "Inspection visits",
        "question": "inspection visits C18",
        "expected_intent": "inspection_visits",
    },
    {
        "name": "General question",
        "question": "What is SpaceEye?",
        "expected_intent": None,
    },
    {
        "name": "Out-of-scope question",
        "question": "What is the weather in Cairo?",
        "expected_intent": None,
    },
]


def run_evaluation():
    results = []

    print("\n" + "=" * 65)
    print("SPACE EYE - HYBRID RAG EVALUATION")
    print("=" * 65)

    for index, test in enumerate(TEST_CASES, start=1):
        print(f"\n[{index}/{len(TEST_CASES)}] {test['name']}")
        print(f"Question: {test['question']}")

        try:
            result = answer_question(
                question=test["question"],
                n_results=5,
            )

            answer = result.get("answer", "")
            actual_intent = result.get("intent")
            evidence_count = result.get("evidence_count", 0)

            answer_ok = bool(answer and answer.strip())

            expected_intent = test["expected_intent"]
            intent_ok = (
                expected_intent is None
                or actual_intent == expected_intent
            )

            result_status = (
                "PASS" if answer_ok and intent_ok else "CHECK"
            )

            item = {
                "name": test["name"],
                "question": test["question"],
                "expected_intent": expected_intent,
                "actual_intent": actual_intent,
                "intent_match": intent_ok,
                "answer_generated": answer_ok,
                "evidence_count": evidence_count,
                "generation_mode": result.get("generation_mode"),
                "status": result_status,
                "answer": answer,
            }

            print(f"Intent: {actual_intent}")
            print(f"Evidence: {evidence_count}")
            print(f"Mode: {result.get('generation_mode')}")
            print(f"Answer generated: {answer_ok}")
            print(f"Status: {result_status}")

            if not intent_ok:
                print(f"Expected intent: {expected_intent}")

            if not evidence_count:
                print("WARNING: No evidence retrieved.")

            if answer:
                print("\nAnswer preview:")
                print(answer[:350].replace("\n", " "))

        except Exception as exc:
            item = {
                "name": test["name"],
                "question": test["question"],
                "status": "ERROR",
                "error": str(exc),
            }
            print(f"ERROR: {exc}")

        results.append(item)

    passed = sum(r["status"] == "PASS" for r in results)
    checked = sum(r["status"] == "CHECK" for r in results)
    errors = sum(r["status"] == "ERROR" for r in results)

    report = {
        "evaluation_date": datetime.now().isoformat(),
        "total_tests": len(results),
        "passed": passed,
        "needs_review": checked,
        "errors": errors,
        "results": results,
    }

    output_path = (
        Path(__file__).resolve().parents[1]
        / "evaluation_results.json"
    )

    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 65)
    print("EVALUATION SUMMARY")
    print("=" * 65)
    print(f"Total tests: {len(results)}")
    print(f"PASS: {passed}")
    print(f"CHECK: {checked}")
    print(f"ERROR: {errors}")
    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    run_evaluation()
