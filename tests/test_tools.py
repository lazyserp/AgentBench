from src.tools import create_ticket
from src.tools import search_policies
from src.tools import get_employee, get_leave_balance

def test_get_employee_by_id():
    matches = get_employee("EMP-101")
    assert len(matches) == 1
    assert matches[0]["name"] == "Sarah Connor"

def test_get_employee_by_name():
    matches = get_employee("Sarah Connor")
    assert len(matches) == 1
    assert matches[0]["id"] == "EMP-101"

def test_get_employee_not_found():
    matches = get_employee("ghost")
    assert matches == []

def test_get_employee_ambiguous():
    matches = get_employee("Sarah")
    assert len(matches) == 2  

def test_get_leave_balance():
    assert get_leave_balance("EMP-101") == {"vacation" : 14, "sick" : 5}
    assert get_leave_balance("ghost") is None

def test_search_policies():
    results = search_policies("equipment")
    assert len(results) > 0
    assert results[0]["id"] == "POL-003"

def test_create_ticket():
    ticket = create_ticket(
        employee_id="EMP-101",
        title="Laptop won't turn on",
        description="Black screen after reboot",
        priority="high"
    )
    
    assert ticket["ticket_id"].startswith("TCK-")
    assert ticket["status"] == "open"
    assert ticket["priority"] == "high"


def test_create_ticket_unknown_employee():
    ticket = create_ticket(
        employee_id="EMP-999",
        title="Access request",
        description="Need VPN access"
    )

    assert "error" in ticket
    assert "not found" in  ticket["error"]

