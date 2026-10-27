import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "employees.json"
POLICIES_FILE = Path(__file__).resolve().parent.parent / "data" / "policies.json"
TICKETS_FILE = Path(__file__).resolve().parent.parent / "data" / "tickets.json"

def get_employee(query : str) ->  dict | None:
    with open(DATA_FILE ,"r") as f:
        employees = json.load(f)
        query = query.strip().lower()

        for emp in employees:
            if emp["id"].lower() == query or emp["name"].lower() == query:
                return emp
        return None 


def get_leave_balance(employee_id  : str) -> dict | None:
    emp = get_employee(employee_id)
    if emp:
        return emp["leave_balance"]
    return None


def search_policies(query : str) -> list[dict] |  None:
    return_list = []

    with open(POLICIES_FILE,"r") as f:
        policies = json.load(f)
        query = query.strip().lower()
    
        for policy in policies:
            if query in policy["title"].lower() or query in policy["content"].lower():
                return_list.append(policy)
    
    return return_list


def create_ticket(employee_id : str , title : str , description : str ,priority : str = "medium") -> dict:
    """ Creates an IT/HR support ticket, Returns the created ticket record"""
    emp = get_employee(employee_id)
    if not emp:
        return {"error" : f"Employee {employee_id} not found"}

    with open(TICKETS_FILE , "r") as f:
        tickets = json.load(f)

    ticket_id = f"TCK-{1000 + len(tickets) + 1}"
    new_ticket = {
        "ticket_id": ticket_id,
        "employee_id": employee_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "open"
    }

    tickets.append(new_ticket)

    with open(TICKETS_FILE,"w") as f:
        json.dump(tickets,f,indent=2)

        
    return new_ticket

    