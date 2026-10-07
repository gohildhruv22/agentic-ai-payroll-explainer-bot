"""
Employee directory API: current user profile, HR-wide list, and single-employee lookup.

Employees may only read their own record unless role is hr_manager or admin.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user, require_role, hash_password
from database import SessionLocal
from models import Employee

router = APIRouter(prefix="/api/employees", tags=["Employees"])


@router.get("/me")
def get_my_profile(current_user: dict = Depends(get_current_user)):
    return {"employee": current_user}


@router.get("")
def list_employees(current_user: dict = Depends(require_role(["hr_manager", "admin"]))):
    db = SessionLocal()
    try:
        employees = db.query(Employee).all()
        return {
            "employees": [
                {
                    "id": e.id,
                    "emp_id": e.emp_id,
                    "name": e.name,
                    "email": e.email,
                    "department": e.department,
                    "designation": e.designation,
                    "grade": e.grade,
                    "location": e.location,
                    "role": e.role,
                    "annual_ctc": e.annual_ctc,
                }
                for e in employees
            ]
        }
    finally:
        db.close()


@router.get("/{employee_id}")
def get_employee(employee_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["hr_manager", "admin"] and current_user["id"] != employee_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {
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
                "role": employee.role,
                "annual_ctc": employee.annual_ctc,
                "tax_regime": employee.tax_regime,
            }
        }
    finally:
        db.close()
