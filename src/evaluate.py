import json
import sys

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent import run_agent


def check_tool_correctness(actual_tools : list[str], expected_tools: list[str]) -> bool:
    """Returns True if the set of actual tools matches the expected tools"""
    return set(actual_tools) == set(expected_tools)

def check_facts_present(response : str, key_facts: list[str]) -> bool:
        """Returns True if all key facts appear in the response (case-insensitive)."""
        response_lower = response.lower()
        for fact in key_facts:
            if isinstance(fact,list):
                if not any(synonym.lower() in response_lower for synonym in fact):
                    return False
            else:
                if fact.lower() not in response_lower:
                    return False
        return True

BENCHMARK_FILE = Path(__file__).resolve().parent.parent / "data" / "benchmark_cases.json"

def run_benchmark():
    total_latency = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0

    with open(BENCHMARK_FILE,"r") as f:
        cases = json.load(f)

    total = len(cases)
    tool_passed  = 0
    facts_passed  = 0
    overall_passed = 0

    print(f"\n--- Running AgentBench ({total} Test Cases) ---\n")

    for case in cases:
        case_id = case['id']
        prompt = case["user_prompt"]
        expected_tools = case["expected_tools"]
        key_facts =  case["ground_truth"]["key_facts"]


        #Run the agent
        result = run_agent(prompt)
        actual_tools = [ t["tool_name"] for t in result["tool_calls"]]
        response_text = result["response"]

        metrics = result.get("metrics",{})
        total_latency += metrics.get("latency_seconds",0)
        total_prompt_tokens += metrics.get("prompt_tokens", 0)
        total_completion_tokens += metrics.get("completion_tokens",0)

        tool_ok = check_tool_correctness(actual_tools,expected_tools)
        facts_ok = check_facts_present(response_text,key_facts)
        case_passed = tool_ok and facts_ok

        if tool_ok:
            tool_passed += 1
        if facts_ok:
            facts_passed += 1
        if case_passed:
            overall_passed += 1
        
        status = "PASS" if case_passed else "FAIL"
        print(f"[ {status} ] [ {case_id} ] ({case['category']}): {prompt[:50]}... ")

        print(f"       Expected tools: {expected_tools} | Actual: {actual_tools}")
        print(f"       Facts present : {facts_ok} (Key facts: {key_facts})")


    print("\n--- Benchmark Summary ---")
    print(f"Total Cases     : {total}")
    print(f"Tool Accuracy   : {tool_passed / total * 100:.1f}%")
    print(f"Fact Accuracy   : {facts_passed / total * 100:.1f}%")
    print(f"Overall Success : {overall_passed / total * 100:.1f}%\n")

    avg_latency = total_latency / total
    total_tokens = total_prompt_tokens + total_completion_tokens
    # Estimated cost in dollars
    estimated_cost = (total_prompt_tokens * 0.00000015) + (total_completion_tokens * 0.00000060)

    print("\n--- Performance & Cost Profiling ---")
    print(f"Avg Latency     : {avg_latency:.2f}s per query")
    print(f"Total Tokens    : {total_tokens:,} (Prompt: {total_prompt_tokens:,} | Completion: {total_completion_tokens:,})")
    print(f"Estimated Cost  : ${estimated_cost:.5f}\n")



if __name__ == "__main__":
    run_benchmark()