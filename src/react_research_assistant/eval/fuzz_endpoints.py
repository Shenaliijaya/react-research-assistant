import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 90

RESULTS_DIR = Path(__file__).resolve().parent / "results"
CSV_PATH = RESULTS_DIR / "stage4_fuzz_results.csv"
JSON_PATH = RESULTS_DIR / "stage4_fuzz_results.json"


@dataclass
class FuzzCase:
    id: str
    method: str
    path: str
    description: str
    expected_statuses: set[int]
    json_body: Any = None
    raw_body: str | None = None
    headers: dict[str, str] | None = None


@dataclass
class FuzzResult:
    id: str
    method: str
    path: str
    description: str
    expected_statuses: list[int]
    actual_status: int | None
    passed: bool
    no_server_error: bool
    response_body: str
    error: str


def fuzz_cases() -> list[FuzzCase]:
    very_long_query = "retention " * 6250

    return [
        FuzzCase(
            id="health_live_datastore",
            method="GET",
            path="/health",
            description="Health endpoint checks live ChromaDB and reports collection size.",
            expected_statuses={200},
        ),
        FuzzCase(
            id="agent_info_live_registry",
            method="GET",
            path="/agent/info",
            description="Agent info endpoint reports live tools, model, and limits.",
            expected_statuses={200},
        ),
        FuzzCase(
            id="agent_malformed_json",
            method="POST",
            path="/agent/query",
            description="Malformed JSON body.",
            expected_statuses={422},
            raw_body='{"query": "hello"',
            headers={"Content-Type": "application/json"},
        ),
        FuzzCase(
            id="agent_missing_query",
            method="POST",
            path="/agent/query",
            description="Missing required query field.",
            expected_statuses={422},
            json_body={"return_trace": True},
        ),
        FuzzCase(
            id="agent_empty_query",
            method="POST",
            path="/agent/query",
            description="Empty query.",
            expected_statuses={422},
            json_body={"query": ""},
        ),
        FuzzCase(
            id="agent_whitespace_query",
            method="POST",
            path="/agent/query",
            description="Whitespace-only query.",
            expected_statuses={422},
            json_body={"query": "   "},
        ),
        FuzzCase(
            id="agent_50000_character_query",
            method="POST",
            path="/agent/query",
            description="50,000-character query must fail validation, not produce a 500.",
            expected_statuses={422},
            json_body={"query": very_long_query},
        ),
        FuzzCase(
            id="agent_emoji_query",
            method="POST",
            path="/agent/query",
            description="Emoji query must not cause a 500.",
            expected_statuses={200},
            json_body={
                "query": "What does Tideline say about retention? 🚀",
                "return_trace": False,
            },
        ),
        FuzzCase(
            id="agent_rtl_query",
            method="POST",
            path="/agent/query",
            description="Right-to-left Unicode query must not cause a 500.",
            expected_statuses={200},
            json_body={
                "query": "ما هي فترة الاحتفاظ الافتراضية في Tideline؟",
                "return_trace": False,
            },
        ),
        FuzzCase(
            id="agent_iteration_zero",
            method="POST",
            path="/agent/query",
            description="Iteration limit below minimum.",
            expected_statuses={422},
            json_body={"query": "What is Tideline?", "max_iterations": 0},
        ),
        FuzzCase(
            id="agent_iteration_999",
            method="POST",
            path="/agent/query",
            description="Iteration limit above maximum.",
            expected_statuses={422},
            json_body={"query": "What is Tideline?", "max_iterations": 999},
        ),
        FuzzCase(
            id="agent_iteration_string",
            method="POST",
            path="/agent/query",
            description="Non-integer iteration limit.",
            expected_statuses={422},
            json_body={"query": "What is Tideline?", "max_iterations": "ten"},
        ),
        FuzzCase(
            id="agent_null_session",
            method="POST",
            path="/agent/query",
            description="Null session identifier is accepted as no session.",
            expected_statuses={200},
            json_body={
                "query": "What is Tideline's storage overage rate?",
                "session_id": None,
                "return_trace": False,
            },
        ),
        FuzzCase(
            id="search_malformed_json",
            method="POST",
            path="/tools/search",
            description="Malformed JSON body for search.",
            expected_statuses={422},
            raw_body='{"query": "France"',
            headers={"Content-Type": "application/json"},
        ),
        FuzzCase(
            id="search_missing_query",
            method="POST",
            path="/tools/search",
            description="Missing query field for search.",
            expected_statuses={422},
            json_body={},
        ),
        FuzzCase(
            id="search_whitespace_query",
            method="POST",
            path="/tools/search",
            description="Whitespace-only search query.",
            expected_statuses={422},
            json_body={"query": "   "},
        ),
        FuzzCase(
            id="retrieve_malformed_json",
            method="POST",
            path="/tools/retrieve",
            description="Malformed JSON body for retrieve.",
            expected_statuses={422},
            raw_body='{"query": "retention"',
            headers={"Content-Type": "application/json"},
        ),
        FuzzCase(
            id="retrieve_missing_query",
            method="POST",
            path="/tools/retrieve",
            description="Missing query field for retrieve.",
            expected_statuses={422},
            json_body={},
        ),
        FuzzCase(
            id="retrieve_whitespace_query",
            method="POST",
            path="/tools/retrieve",
            description="Whitespace-only retrieve query.",
            expected_statuses={422},
            json_body={"query": "   "},
        ),
        FuzzCase(
            id="retrieve_result_count_zero",
            method="POST",
            path="/tools/retrieve",
            description="Retrieve result_count below minimum.",
            expected_statuses={422},
            json_body={"query": "retention", "result_count": 0},
        ),
        FuzzCase(
            id="retrieve_result_count_string",
            method="POST",
            path="/tools/retrieve",
            description="Non-integer retrieve result_count.",
            expected_statuses={422},
            json_body={"query": "retention", "result_count": "three"},
        ),
        FuzzCase(
            id="calculate_malformed_json",
            method="POST",
            path="/tools/calculate",
            description="Malformed JSON body for calculate.",
            expected_statuses={422},
            raw_body='{"expression": "1 + 1"',
            headers={"Content-Type": "application/json"},
        ),
        FuzzCase(
            id="calculate_missing_expression",
            method="POST",
            path="/tools/calculate",
            description="Missing calculator expression.",
            expected_statuses={422},
            json_body={},
        ),
        FuzzCase(
            id="calculate_divide_by_zero",
            method="POST",
            path="/tools/calculate",
            description="Division by zero returns clean client error.",
            expected_statuses={400, 422},
            json_body={"expression": "1 / 0"},
        ),
        FuzzCase(
            id="calculate_huge_exponent",
            method="POST",
            path="/tools/calculate",
            description="Huge exponent must fail cleanly without hanging.",
            expected_statuses={400, 422},
            json_body={"expression": "2 ** 999999999"},
        ),
        FuzzCase(
            id="calculate_code_injection",
            method="POST",
            path="/tools/calculate",
            description="Python code injection must be rejected.",
            expected_statuses={400, 422},
            json_body={"expression": "__import__('os').system('dir')"},
        ),
        FuzzCase(
            id="calculate_string_literal",
            method="POST",
            path="/tools/calculate",
            description="String expression must be rejected.",
            expected_statuses={400, 422},
            json_body={"expression": "\"hello\""},
        ),
    ]


def run_case(case: FuzzCase) -> FuzzResult:
    url = f"{BASE_URL}{case.path}"

    try:
        if case.method == "GET":
            response = requests.get(url, timeout=TIMEOUT_SECONDS)
        elif case.raw_body is not None:
            response = requests.request(
                case.method,
                url,
                data=case.raw_body,
                headers=case.headers,
                timeout=TIMEOUT_SECONDS,
            )
        else:
            response = requests.request(
                case.method,
                url,
                json=case.json_body,
                timeout=TIMEOUT_SECONDS,
            )

        actual_status = response.status_code
        response_body = response.text[:1000]

        return FuzzResult(
            id=case.id,
            method=case.method,
            path=case.path,
            description=case.description,
            expected_statuses=sorted(case.expected_statuses),
            actual_status=actual_status,
            passed=actual_status in case.expected_statuses,
            no_server_error=not (500 <= actual_status < 600),
            response_body=response_body,
            error="",
        )
    except requests.RequestException as exc:
        return FuzzResult(
            id=case.id,
            method=case.method,
            path=case.path,
            description=case.description,
            expected_statuses=sorted(case.expected_statuses),
            actual_status=None,
            passed=False,
            no_server_error=True,
            response_body="",
            error=str(exc),
        )


def write_results(results: list[FuzzResult]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with CSV_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "id",
                "method",
                "path",
                "description",
                "expected_statuses",
                "actual_status",
                "passed",
                "no_server_error",
                "response_body",
                "error",
            ]
        )

        for result in results:
            writer.writerow(
                [
                    result.id,
                    result.method,
                    result.path,
                    result.description,
                    " or ".join(map(str, result.expected_statuses)),
                    result.actual_status,
                    result.passed,
                    result.no_server_error,
                    result.response_body,
                    result.error,
                ]
            )

    with JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            [
                {
                    "id": result.id,
                    "method": result.method,
                    "path": result.path,
                    "description": result.description,
                    "expected_statuses": result.expected_statuses,
                    "actual_status": result.actual_status,
                    "passed": result.passed,
                    "no_server_error": result.no_server_error,
                    "response_body": result.response_body,
                    "error": result.error,
                }
                for result in results
            ],
            file,
            indent=2,
            ensure_ascii=False,
        )


def main() -> None:
    print("Stage 4 Part C endpoint fuzzing")
    print(f"Target API: {BASE_URL}\n")

    results = [run_case(case) for case in fuzz_cases()]

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(
            f"[{label}] {result.id} | expected={result.expected_statuses} | "
            f"actual={result.actual_status} | no_500={result.no_server_error}"
        )

        if result.error:
            print(f"  ERROR: {result.error}")

    passed_count = sum(result.passed for result in results)
    server_errors = sum(not result.no_server_error for result in results)

    write_results(results)

    print("\n" + "=" * 80)
    print(f"TOTAL: {passed_count}/{len(results)} cases passed")
    print(f"Server errors (5xx): {server_errors}")
    print(f"CSV results: {CSV_PATH}")
    print(f"JSON results: {JSON_PATH}")


if __name__ == "__main__":
    main()