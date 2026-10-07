"""
Deterministic payroll checks used as a critic layer for agent outputs.
"""
from tools.payroll_db_fetch import payroll_db_fetch


def deterministic_payroll_check(employee_id: int, month: str) -> dict:
    data = payroll_db_fetch(employee_id=employee_id, month=month)
    if not data.get("success"):
        return {"success": False, "error": data.get("error", "Record not found")}

    rec = data["record"]
    expected_total = round(
        float(rec.get("pf_employee", 0))
        + float(rec.get("esic_employee", 0))
        + float(rec.get("professional_tax", 0))
        + float(rec.get("tds", 0)),
        2,
    )
    expected_net = round(float(rec.get("gross_pay", 0)) - expected_total, 2)

    total_gap = round(abs(float(rec.get("total_deductions", 0)) - expected_total), 2)
    net_gap = round(abs(float(rec.get("net_pay", 0)) - expected_net), 2)
    is_consistent = total_gap <= 2 and net_gap <= 2

    return {
        "success": True,
        "month": month,
        "is_consistent": is_consistent,
        "expected_total_deductions": expected_total,
        "stored_total_deductions": float(rec.get("total_deductions", 0)),
        "expected_net_pay": expected_net,
        "stored_net_pay": float(rec.get("net_pay", 0)),
        "total_gap": total_gap,
        "net_gap": net_gap,
    }

