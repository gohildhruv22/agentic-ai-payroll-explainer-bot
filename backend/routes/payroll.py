"""
Payroll API: monthly salary breakdown, history, and PDF payslip download.

Uses SalaryRecord + Employee; access rules mirror employees (self or HR/admin).
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from auth import get_current_user, require_role
from database import SessionLocal
from models import SalaryRecord, Employee
from tools.payslip_generator import payslip_generator

router = APIRouter(prefix="/api/payroll", tags=["Payroll"])


@router.get("/{employee_id}/{month}")
def get_salary_record(employee_id: int, month: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["hr_manager", "admin"] and current_user["id"] != employee_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db = SessionLocal()
    try:
        record = db.query(SalaryRecord).filter(
            SalaryRecord.employee_id == employee_id,
            SalaryRecord.month == month
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="Salary record not found")

        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        return {
            "employee_name": employee.name if employee else "Unknown",
            "emp_id": employee.emp_id if employee else "N/A",
            "record": {
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
        }
    finally:
        db.close()


@router.get("/{employee_id}/history")
def get_salary_history(employee_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["hr_manager", "admin"] and current_user["id"] != employee_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db = SessionLocal()
    try:
        records = db.query(SalaryRecord).filter(
            SalaryRecord.employee_id == employee_id
        ).order_by(SalaryRecord.month.desc()).all()

        employee = db.query(Employee).filter(Employee.id == employee_id).first()

        return {
            "employee_name": employee.name if employee else "Unknown",
            "records": [
                {
                    "month": r.month,
                    "gross_pay": r.gross_pay,
                    "total_deductions": r.total_deductions,
                    "net_pay": r.net_pay,
                    "basic": r.basic,
                    "hra": r.hra,
                    "tds": r.tds,
                    "pf_employee": r.pf_employee,
                    "bonus": r.bonus,
                    "lop_days": r.lop_days,
                }
                for r in records
            ]
        }
    finally:
        db.close()


# Streams a generated PDF from payslip_generator (temp file on disk)
@router.get("/download/{emp_id}/{month}")
def download_payslip(emp_id: str, month: str, current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.emp_id == emp_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        if current_user["role"] not in ["hr_manager", "admin"] and current_user["id"] != employee.id:
            raise HTTPException(status_code=403, detail="Access denied")

        result = payslip_generator(employee.id, month)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Failed to generate payslip"))

        filepath = result["file_path"]
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Payslip file not found")

        return FileResponse(
            path=filepath,
            filename=f"payslip_{emp_id}_{month}.pdf",
            media_type="application/pdf"
        )
    finally:
        db.close()
