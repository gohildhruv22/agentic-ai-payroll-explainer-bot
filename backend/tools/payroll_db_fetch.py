"""
Tool: read SalaryRecord rows for an employee (one month or full history) for AI tools.
"""
from database import SessionLocal
from models import SalaryRecord, Employee


def payroll_db_fetch(employee_id: int, month: str = None, fields: list = None) -> dict:
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"error": "Employee not found", "success": False}

        query = db.query(SalaryRecord).filter(SalaryRecord.employee_id == employee_id)

        if month:
            record = query.filter(SalaryRecord.month == month).first()
            if not record:
                return {
                    "error": f"No salary record found for employee {employee.name} for month {month}",
                    "success": False
                }
            return {
                "success": True,
                "employee_name": employee.name,
                "emp_id": employee.emp_id,
                "record": _salary_to_dict(record)
            }
        else:
            records = query.order_by(SalaryRecord.month.desc()).all()
            if not records:
                return {"error": "No salary records found", "success": False}
            return {
                "success": True,
                "employee_name": employee.name,
                "emp_id": employee.emp_id,
                "records": [_salary_to_dict(r) for r in records]
            }
    except Exception as e:
        return {"error": str(e), "success": False}
    finally:
        db.close()


def _salary_to_dict(record: SalaryRecord) -> dict:
    return {
        "month": record.month,
        "ctc": record.ctc,
        "basic": record.basic,
        "hra": record.hra,
        "da": record.da,
        "special_allowance": record.special_allowance,
        "medical": record.medical,
        "lta": record.lta,
        "pf_employee": record.pf_employee,
        "pf_employer": record.pf_employer,
        "esic_employee": record.esic_employee,
        "esic_employer": record.esic_employer,
        "professional_tax": record.professional_tax,
        "tds": record.tds,
        "lop_days": record.lop_days,
        "lop_deduction": record.lop_deduction,
        "gross_pay": record.gross_pay,
        "total_deductions": record.total_deductions,
        "net_pay": record.net_pay,
        "bonus": record.bonus,
        "arrears": record.arrears,
        "overtime": record.overtime,
    }
