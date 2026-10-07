"""
Builds a PDF payslip (ReportLab) for one employee/month and returns a temp file path for download.
"""
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from database import SessionLocal
from models import SalaryRecord, Employee


def payslip_generator(employee_id: int, month: str) -> dict:
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"error": "Employee not found", "success": False}

        record = db.query(SalaryRecord).filter(
            SalaryRecord.employee_id == employee_id,
            SalaryRecord.month == month
        ).first()
        if not record:
            return {"error": f"No salary record for {month}", "success": False}

        os.makedirs("payslips", exist_ok=True)
        filename = f"payslips/payslip_{employee.emp_id}_{month}.pdf"
        _generate_pdf(employee, record, filename)

        return {
            "success": True,
            "message": f"Payslip generated for {employee.name} ({month})",
            "file_path": filename,
            "download_url": f"/api/payroll/download/{employee.emp_id}/{month}",
        }
    except Exception as e:
        return {"error": str(e), "success": False}
    finally:
        db.close()


def _generate_pdf(employee: Employee, record: SalaryRecord, filename: str):
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18,
                                  textColor=colors.HexColor('#1e3a5f'), spaceAfter=4)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10,
                                     textColor=colors.HexColor('#666666'), alignment=TA_CENTER)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=11,
                                   textColor=colors.white, fontName='Helvetica-Bold')
    normal_style = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=9)
    bold_style = ParagraphStyle('BoldCustom', parent=styles['Normal'], fontSize=10,
                                 fontName='Helvetica-Bold')

    elements.append(Paragraph("MAQ SOFTWARE PVT. LTD.", title_style))
    elements.append(Paragraph(f"Payslip for the month of {month_name(record.month)}", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1e3a5f')))
    elements.append(Spacer(1, 10))

    emp_data = [
        ["Employee Name", employee.name, "Employee ID", employee.emp_id],
        ["Department", employee.department, "Designation", employee.designation],
        ["Location", employee.location, "Grade", employee.grade],
        ["PAN", employee.pan_number or "N/A", "Bank A/C", mask_account(employee.bank_account)],
    ]
    emp_table = Table(emp_data, colWidths=[90, 150, 90, 150])
    emp_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#1e3a5f')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 15))

    earnings = [
        ["Earnings", "Amount (₹)", "Deductions", "Amount (₹)"],
        ["Basic Salary", fmt(record.basic), "PF (Employee)", fmt(record.pf_employee)],
        ["House Rent Allowance", fmt(record.hra), "ESIC (Employee)", fmt(record.esic_employee)],
        ["Dearness Allowance", fmt(record.da), "Professional Tax", fmt(record.professional_tax)],
        ["Special Allowance", fmt(record.special_allowance), "TDS", fmt(record.tds)],
        ["Medical Allowance", fmt(record.medical), "LOP Deduction", fmt(record.lop_deduction)],
        ["LTA", fmt(record.lta), "", ""],
        ["Bonus", fmt(record.bonus), "", ""],
        ["Arrears", fmt(record.arrears), "", ""],
        ["Overtime", fmt(record.overtime), "", ""],
    ]

    salary_table = Table(earnings, colWidths=[130, 100, 130, 100])
    salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(salary_table)
    elements.append(Spacer(1, 15))

    total_earnings = (record.basic + record.hra + record.da + record.special_allowance +
                      record.medical + record.lta + record.bonus + record.arrears + record.overtime)
    summary = [
        ["Gross Earnings", fmt(total_earnings), "Total Deductions", fmt(record.total_deductions)],
        ["", "", "", ""],
        ["NET PAY", "", "", fmt(record.net_pay)],
    ]
    summary_table = Table(summary, colWidths=[130, 100, 130, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f4f8')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('SPAN', (0, 2), (2, 2)),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(
        "This is a system-generated payslip. For any discrepancies, please contact HR.",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.HexColor('#999999'), alignment=TA_CENTER)
    ))

    doc.build(elements)


def month_name(month_str: str) -> str:
    months = {
        "01": "January", "02": "February", "03": "March", "04": "April",
        "05": "May", "06": "June", "07": "July", "08": "August",
        "09": "September", "10": "October", "11": "November", "12": "December"
    }
    parts = month_str.split("-")
    if len(parts) == 2:
        return f"{months.get(parts[1], parts[1])} {parts[0]}"
    return month_str


def fmt(amount: float) -> str:
    if amount == 0:
        return "-"
    return f"{amount:,.0f}"


def mask_account(account: str) -> str:
    if not account:
        return "N/A"
    if len(account) > 4:
        return "XXXX" + account[-4:]
    return account
