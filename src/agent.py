import os
import json
import time
from dotenv import load_dotenv
from groq import Groq

from src.tools import get_employee,get_leave_balance,search_policies,create_ticket

load_dotenv()

TOOLS = [
    {
        "type" : "function",
        "function" : {
            "name" : "get_employee",
            "description" : "Look up an employee profile by ID (e.g. 'EMP-101') or full name.",
            "parameters" : {
                "type" : "object",
                "properties" :{
                    "query" : {
                        "type" : "string",
                        "description" : "Employee ID (e.g. 'EMP-101') or full name"
                    }
                },
                "required" : ["query"]
            }
        }
    },
    {
        "type" : "function",
        "function" : {
            "name" : "get_leave_balance",
            "description" : "Retrieve remaining vacation and sick leave days for an employee by ID.",
            "parameters" : {
                "type" : "object",
                "properties": {
                    "employee_id" : {
                        "type" : "string",
                        "description" : "The employee ID whose leave details are required, e.g. 'EMP-101'"
                    }
                },
                "required" : ["employee_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_policies",
            "description": "Search company HR, IT, and travel policy documents by keywords or topics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The policy topic or keywords (e.g. 'PTO rollover', 'equipment reimbursement', 'sick leave')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create an IT or HR support ticket for an employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "The ID of the employee creating the ticket, e.g. 'EMP-101'"
                    },
                    "title": {
                        "type": "string",
                        "description": "Short summary of the issue"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue or request"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "Priority level of the ticket"
                    }
                },
                "required": ["employee_id", "title", "description"]
            }
        }
    }

]

TOOL_MAP = {
    "get_employee": get_employee,
    "get_leave_balance": get_leave_balance,
    "search_policies": search_policies,
    "create_ticket": create_ticket,
}

SYSTEM_PROMPT = """You are an HR and IT support assistant for an enterprise.
Guidelines:
1. Always use the available tools to look up factual information (employee records, leave balances, company policies) and to perform actions (create tickets).
2. Never invent, hallucinate, or guess employee details or policy rules.
3. If a tool requires an employee ID and you only have their name, look up the employee first using get_employee.
4. If a request is missing critical information or is ambiguous, ask the user a clarifying question instead of making assumptions.
5. Be concise, polite, and helpful in your final response.
"""


def run_agent(user_prompt: str, model: str = "openai/gpt-oss-120b", max_step: int = 5, verbose: bool = False) -> dict:
    client = Groq()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    recorded_tool_calls = []

    if verbose:
        print(f"\n{'='*20} AGENT EXECUTION TRACE {'='*20}")
        print(f"[USER PROMPT]: {user_prompt}")

    start_time = time.perf_counter()
    total_prompt_tokens, total_completion_tokens = 0,0


    for step in range(1, max_step + 1):
        if verbose:
            print(f"\n--- [Turn {step}]: Calling LLM ({model}) ---")

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.0
        )

        response_message = response.choices[0].message

        if response.usage:
            total_prompt_tokens += response.usage.prompt_tokens
            total_completion_tokens += response.usage.completion_tokens

        # Case A: Model didn't call any tools, it answered the user directly
        if not response_message.tool_calls:
            if verbose:
                print(f"--- [Turn {step}]: LLM decided to answer directly ---")
                print(f"[FINAL ANSWER]: {response_message.content}\n{'='*58}\n")
            latency_seconds = round(time.perf_counter() - start_time, 2)

            return {
                "response": response_message.content,
                "tool_calls": recorded_tool_calls,
                "metrics": {
                    "latency_seconds": latency_seconds,
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                    "total_tokens": total_prompt_tokens + total_completion_tokens
                }
            }

        # Case B: Model requested one or more tool calls
        messages.append(response_message)

        if verbose:
            print(f"--- [Turn {step}]: LLM requested {len(response_message.tool_calls)} tool call(s) ---")

        for tool_call in response_message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            if verbose:
                print(f"    [LLM REQUEST]: {fn_name}({fn_args})")

            if fn_name in TOOL_MAP:
                tool_output = TOOL_MAP[fn_name](**fn_args)
            else:
                tool_output = {"error": f"Tool '{fn_name}' not found"}

            if verbose:
                print(f"   [TOOL OUTPUT]: {tool_output}")

            recorded_tool_calls.append({
                "tool_name": fn_name,
                "arguments": fn_args,
                "output": tool_output
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_output)
            })

    latency_seconds = round(time.perf_counter() - start_time, 2)
    return {
        "response": response_message.content or "Reached maximum step limit.",
        "tool_calls": recorded_tool_calls,
        "metrics": {
            "latency_seconds": latency_seconds,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens
        }
    }
