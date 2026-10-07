"""
Tool: load one employee record by id, emp_id, or email for agents and orchestrator context.
"""
import json
from database import SessionLocal
from models import Employee


def employee_profile_fetch(employee_id: int = None, emp_id: str = None, email: str = None) -> dict:
    db = SessionLocal()
    try:
        employee = None
        if employee_id:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
        elif emp_id:
            employee = db.query(Employee).filter(Employee.emp_id == emp_id).first()
        elif email:
            employee = db.query(Employee).filter(Employee.email == email).first()

        if not employee:
            return {"error": "Employee not found", "success": False}

        return {
            "success": True,
            "employee": {
                "id": employee.id,
                "emp_id": employee.emp_id,
                "name": employee.name,
                "email": employee.email,
                "department": employee.department,
                "designation": employee.designation,
                "grade": employee.grade,
                "location": employee.location,
                "city_tier": employee.city_tier,
                "joining_date": employee.joining_date,
                "manager_name": employee.manager_name,
                "manager_email": employee.manager_email,
                "role": employee.role,
                "annual_ctc": employee.annual_ctc,
                "tax_regime": employee.tax_regime,
                "rent_paid_monthly": employee.rent_paid_monthly,
            }
        }
    except Exception as e:
        return {"error": str(e), "success": False}
    finally:
        db.close()
