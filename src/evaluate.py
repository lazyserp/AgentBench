import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent import run_agent

BENCHMARK_FILE = Path(__file__).resolve().parent.parent / "data" / "benchmark_cases.json"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def check_tool_correctness(actual_tools: list[str], expected_tools: list[str]) -> bool:
    """Returns True if the set of actual tools matches the expected tools."""
    return set(actual_tools) == set(expected_tools)


def check_facts_present(response: str, key_facts: list) -> bool:
    """
    Returns True if all required facts are present in response.
    Supports both plain strings and synonym lists:
      - 'Product': must be present
      - ['rollover', 'carry over']: at least one must be present
    """
    response_lower = response.lower()
    for fact in key_facts:
        if isinstance(fact, list):
            if not any(synonym.lower() in response_lower for synonym in fact):
                return False
        else:
            if fact.lower() not in response_lower:
                return False
    return True


def save_evaluation_artifacts(summary: dict, case_results: list):
    """Saves latest_run.json and generates a readable report.md."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # 1. Machine-readable JSON artifact
    artifact_data = {
        "timestamp": timestamp,
        "summary": summary,
        "cases": case_results
    }
    with open(RESULTS_DIR / "latest_run.json", "w", encoding="utf-8") as f:
        json.dump(artifact_data, f, indent=2)

    # 2. Human-readable Markdown Report
    report_lines = [
        "# AgentBench Evaluation Report",
        f"\n**Run Timestamp**: `{timestamp}`\n",
        "## 1. Executive Summary\n",
        "| Metric | Value |",
        "| :--- | :--- |",
        f"| **Total Test Cases** | {summary['total_cases']} |",
        f"| **Tool Selection Accuracy** | {summary['tool_accuracy']:.1f}% |",
        f"| **Fact Grounding Accuracy** | {summary['fact_accuracy']:.1f}% |",
        f"| **Overall Task Success Rate** | {summary['overall_success']:.1f}% |",
        f"| **Average Latency** | {summary['avg_latency_s']:.2f}s |",
        f"| **Total Tokens Consumed** | {summary['total_tokens']:,} |",
        f"| **Estimated Cost** | ${summary['estimated_cost_usd']:.5f} |\n",
        "## 2. Failure Analysis\n",
        "| ID | Category | User Query | Failure Details |",
        "| :--- | :--- | :--- | :--- |"
    ]

    failed_cases = [c for c in case_results if not c["passed"]]
    if not failed_cases:
        report_lines.append("\n*All test cases passed! Zero failures recorded.*")
    else:
        for c in failed_cases:
            reason = []
            if not c["tool_ok"]:
                reason.append(f"Tool Mismatch (Expected: {c['expected_tools']}, Got: {c['actual_tools']})")
            if not c["facts_ok"]:
                reason.append("Missing Key Facts")
            reason_str = "; ".join(reason)
            query_snippet = c["prompt"][:45] + "..." if len(c["prompt"]) > 45 else c["prompt"]
            report_lines.append(f"| `{c['id']}` | `{c['category']}` | {query_snippet} | {reason_str} |")

    with open(RESULTS_DIR / "report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"[ARTIFACTS SAVED] -> {RESULTS_DIR / 'latest_run.json'}")
    print(f"[REPORT GENERATED] -> {RESULTS_DIR / 'report.md'}\n")


def run_benchmark():
    total_latency = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0

    with open(BENCHMARK_FILE, "r") as f:
        cases = json.load(f)

    total = len(cases)
    tool_passed = 0
    facts_passed = 0
    overall_passed = 0
    case_results = []

    print(f"\n--- Running AgentBench ({total} Test Cases) ---\n")

    for case in cases:
        case_id = case["id"]
        prompt = case["user_prompt"]
        expected_tools = case["expected_tools"]
        key_facts = case["ground_truth"]["key_facts"]

        # Run the agent
        result = run_agent(prompt)
        actual_tools = [t["tool_name"] for t in result["tool_calls"]]
        response_text = result["response"]

        metrics = result.get("metrics", {})
        total_latency += metrics.get("latency_seconds", 0)
        total_prompt_tokens += metrics.get("prompt_tokens", 0)
        total_completion_tokens += metrics.get("completion_tokens", 0)

        tool_ok = check_tool_correctness(actual_tools, expected_tools)
        facts_ok = check_facts_present(response_text, key_facts)
        case_passed = tool_ok and facts_ok

        if tool_ok:
            tool_passed += 1
        if facts_ok:
            facts_passed += 1
        if case_passed:
            overall_passed += 1

        status = "PASS" if case_passed else "FAIL"
        print(f"[ {status} ] [ {case_id} ] ({case['category']}): {prompt[:50]}... ")

        if not case_passed:
            print(f"       Expected tools: {expected_tools} | Actual: {actual_tools}")
            print(f"       Facts present : {facts_ok} (Key facts: {key_facts})")
            print(f"       Agent Response: \"{response_text.strip()}\"\n")

        case_results.append({
            "id": case_id,
            "category": case["category"],
            "prompt": prompt,
            "expected_tools": expected_tools,
            "actual_tools": actual_tools,
            "tool_ok": tool_ok,
            "facts_ok": facts_ok,
            "passed": case_passed,
            "response": response_text
        })

    print("\n--- Benchmark Summary ---")
    print(f"Total Cases     : {total}")
    print(f"Tool Accuracy   : {tool_passed / total * 100:.1f}%")
    print(f"Fact Accuracy   : {facts_passed / total * 100:.1f}%")
    print(f"Overall Success : {overall_passed / total * 100:.1f}%\n")

    avg_latency = total_latency / total
    total_tokens = total_prompt_tokens + total_completion_tokens
    estimated_cost = (total_prompt_tokens * 0.00000015) + (total_completion_tokens * 0.00000060)

    print("\n--- Performance & Cost Profiling ---")
    print(f"Avg Latency     : {avg_latency:.2f}s per query")
    print(f"Total Tokens    : {total_tokens:,} (Prompt: {total_prompt_tokens:,} | Completion: {total_completion_tokens:,})")
    print(f"Estimated Cost  : ${estimated_cost:.5f}\n")

    summary = {
        "total_cases": total,
        "tool_accuracy": tool_passed / total * 100,
        "fact_accuracy": facts_passed / total * 100,
        "overall_success": overall_passed / total * 100,
        "avg_latency_s": avg_latency,
        "total_tokens": total_tokens,
        "estimated_cost_usd": estimated_cost
    }
    save_evaluation_artifacts(summary, case_results)


if __name__ == "__main__":
    run_benchmark()
