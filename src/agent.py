import os
import json
from dotenv import load_dotenv
from groq import Groq
from src.tools import get_employee, get_leave_balance, search_policies, create_ticket


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_employee",
            "description": "Look up an employee profile by ID (e.g. 'EMP-101') or full name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Employee ID (e.g. 'EMP-101') or full name (e.g. 'Sarah Connor')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_leave_balance",
            "description": "Retrieve remaining vacation and sick leave days for an employee by their exact ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "The exact ID of the employee, e.g. 'EMP-101'"
                    }
                },
                "required": ["employee_id"]
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
                    1. Always use available tools to look up factual info (employees, leave balances, policies) and take actions (tickets).
                    2. Never invent, hallucinate, or guess employee details or policy rules.
                    3. If a tool requires an employee ID and you only have their name, look up the employee first using get_employee.
                    4. If a request is missing critical information or is ambiguous, ask the user a clarifying question instead of guessing.
                    5. Be concise and polite in your final response.
                """
