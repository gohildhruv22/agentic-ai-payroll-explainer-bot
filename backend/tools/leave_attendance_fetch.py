"""
Tool: read LeaveBalance and optional monthly AttendanceRecord for policy/payroll agents.
"""
from database import SessionLocal
from models import LeaveBalance, AttendanceRecord, Employee


def leave_attendance_fetch(employee_id: int, month: str = None) -> dict:
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"error": "Employee not found", "success": False}

        leave = db.query(LeaveBalance).filter(LeaveBalance.employee_id == employee_id).first()
        leave_data = None
        if leave:
            leave_data = {
                "earned_leave": leave.earned_leave,
                "sick_leave": leave.sick_leave,
                "casual_leave": leave.casual_leave,
                "maternity_leave": leave.maternity_leave,
                "paternity_leave": leave.paternity_leave,
                "compensatory_off": leave.compensatory_off,
                "lop_days_ytd": leave.lop_days_ytd,
                "total_available": (
                    leave.earned_leave + leave.sick_leave +
                    leave.casual_leave + leave.compensatory_off
                ),
            }

        attendance_data = []
        query = db.query(AttendanceRecord).filter(AttendanceRecord.employee_id == employee_id)
        if month:
            query = query.filter(AttendanceRecord.month == month)
        records = query.order_by(AttendanceRecord.month.desc()).all()

        for rec in records:
            attendance_data.append({
                "month": rec.month,
                "working_days": rec.working_days,
                "present_days": rec.present_days,
                "absent_days": rec.absent_days,
                "lop_days": rec.lop_days,
                "half_days": rec.half_days,
            })

        return {
            "success": True,
            "employee_name": employee.name,
            "leave_balance": leave_data,
            "attendance": attendance_data,
        }
    except Exception as e:
        return {"error": str(e), "success": False}
    finally:
        db.close()
