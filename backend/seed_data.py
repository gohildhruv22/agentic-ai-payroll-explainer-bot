"""
One-time (or dev) database seeding script.

Drops and recreates tables, inserts demo employees, salary history, leave balances, attendance,
policies, sample disputes, etc. Run manually: `python seed_data.py`. Not used in production deploys.
"""
import math
from datetime import datetime
from database import engine, Base, SessionLocal
from models import (
    Employee, SalaryRecord, LeaveBalance, AttendanceRecord,
    DisputeTicket, PolicyDocument, Notification,
    HumanApprovalRequest, AutonomousEvent, SlaIncident, AutonomousJobRun
)
from auth import hash_password


# Helper: approximate monthly TDS under new tax regime slabs (for demo salary rows)
def compute_monthly_tds_new_regime(annual_gross):
    taxable = max(0, annual_gross - 75000)
    if taxable <= 1200000:
        return 0
    tax = 0
    slabs = [
        (400000, 0.00), (400000, 0.05), (400000, 0.10),
        (400000, 0.15), (400000, 0.20), (400000, 0.25), (math.inf, 0.30),
    ]
    remaining = taxable
    for slab_amount, rate in slabs:
        if remaining <= 0:
            break
        amount = min(remaining, slab_amount)
        tax += amount * rate
        remaining -= amount
    tax *= 1.04
    return round(tax / 12)


def seed():
    # Full reset — wipes existing data
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        employees_data = [
            {"emp_id": "EMP001", "name": "Rahul Sharma", "email": "rahul.sharma@company.com",
             "department": "Engineering", "designation": "Senior Software Engineer", "grade": "L5",
             "location": "Mumbai", "city_tier": "metro", "joining_date": "2020-06-15",
             "manager_name": "Rajesh Nair", "manager_email": "rajesh.nair@company.com",
             "role": "employee", "annual_ctc": 1800000, "pan": "ABCPS1234K",
             "bank": "1234567890", "regime": "new", "rent": 20000},
            {"emp_id": "EMP002", "name": "Priya Patel", "email": "priya.patel@company.com",
             "department": "HR", "designation": "HR Manager", "grade": "L6",
             "location": "Mumbai", "city_tier": "metro", "joining_date": "2019-03-01",
             "manager_name": "Neha Agarwal", "manager_email": "neha.agarwal@company.com",
             "role": "hr_manager", "annual_ctc": 1500000, "pan": "BCPPP5678L",
             "bank": "9876543210", "regime": "old", "rent": 18000},
            {"emp_id": "EMP003", "name": "Amit Kumar", "email": "amit.kumar@company.com",
             "department": "Engineering", "designation": "Software Engineer", "grade": "L4",
             "location": "Bangalore", "city_tier": "metro", "joining_date": "2022-01-10",
             "manager_name": "Rahul Sharma", "manager_email": "rahul.sharma@company.com",
             "role": "employee", "annual_ctc": 1000000, "pan": "CKPKA9012M",
             "bank": "1122334455", "regime": "new", "rent": 15000},
            {"emp_id": "EMP004", "name": "Sneha Reddy", "email": "sneha.reddy@company.com",
             "department": "Finance", "designation": "Financial Analyst", "grade": "L4",
             "location": "Hyderabad", "city_tier": "metro", "joining_date": "2021-07-20",
             "manager_name": "Kavita Iyer", "manager_email": "kavita.iyer@company.com",
             "role": "employee", "annual_ctc": 1200000, "pan": "DRPKS3456N",
             "bank": "5566778899", "regime": "new", "rent": 12000},
            {"emp_id": "EMP005", "name": "Vikram Singh", "email": "vikram.singh@company.com",
             "department": "Sales", "designation": "Sales Manager", "grade": "L5",
             "location": "Delhi", "city_tier": "metro", "joining_date": "2020-11-05",
             "manager_name": "Priya Patel", "manager_email": "priya.patel@company.com",
             "role": "employee", "annual_ctc": 1400000, "pan": "ESPVS7890P",
             "bank": "6677889900", "regime": "new", "rent": 22000},
            {"emp_id": "EMP006", "name": "Anjali Gupta", "email": "anjali.gupta@company.com",
             "department": "HR", "designation": "HR Executive", "grade": "L3",
             "location": "Mumbai", "city_tier": "metro", "joining_date": "2023-02-14",
             "manager_name": "Priya Patel", "manager_email": "priya.patel@company.com",
             "role": "employee", "annual_ctc": 700000, "pan": "FGPAG1234Q",
             "bank": "7788990011", "regime": "new", "rent": 10000},
            {"emp_id": "EMP007", "name": "Rajesh Nair", "email": "rajesh.nair@company.com",
             "department": "Engineering", "designation": "Tech Lead", "grade": "L7",
             "location": "Bangalore", "city_tier": "metro", "joining_date": "2017-08-01",
             "manager_name": "Neha Agarwal", "manager_email": "neha.agarwal@company.com",
             "role": "hr_manager", "annual_ctc": 2200000, "pan": "GHPRN5678R",
             "bank": "8899001122", "regime": "new", "rent": 30000},
            {"emp_id": "EMP008", "name": "Meera Joshi", "email": "meera.joshi@company.com",
             "department": "Operations", "designation": "Operations Manager", "grade": "L5",
             "location": "Pune", "city_tier": "non_metro", "joining_date": "2021-04-12",
             "manager_name": "Neha Agarwal", "manager_email": "neha.agarwal@company.com",
             "role": "employee", "annual_ctc": 1300000, "pan": "HIPMJ9012S",
             "bank": "9900112233", "regime": "old", "rent": 14000},
            {"emp_id": "EMP009", "name": "Arjun Menon", "email": "arjun.menon@company.com",
             "department": "Engineering", "designation": "Junior Developer", "grade": "L2",
             "location": "Chennai", "city_tier": "metro", "joining_date": "2024-06-01",
             "manager_name": "Rahul Sharma", "manager_email": "rahul.sharma@company.com",
             "role": "employee", "annual_ctc": 600000, "pan": "IJPAM3456T",
             "bank": "1010202030", "regime": "new", "rent": 8000},
            {"emp_id": "EMP010", "name": "Kavita Iyer", "email": "kavita.iyer@company.com",
             "department": "Finance", "designation": "Accounts Manager", "grade": "L6",
             "location": "Mumbai", "city_tier": "metro", "joining_date": "2018-10-15",
             "manager_name": "Neha Agarwal", "manager_email": "neha.agarwal@company.com",
             "role": "employee", "annual_ctc": 1600000, "pan": "JKPKI7890U",
             "bank": "3030404050", "regime": "old", "rent": 25000},
            {"emp_id": "EMP011", "name": "Sanjay Verma", "email": "sanjay.verma@company.com",
             "department": "Sales", "designation": "Sales Executive", "grade": "L3",
             "location": "Jaipur", "city_tier": "non_metro", "joining_date": "2023-09-01",
             "manager_name": "Vikram Singh", "manager_email": "vikram.singh@company.com",
             "role": "employee", "annual_ctc": 800000, "pan": "KLPSV1234V",
             "bank": "5050606070", "regime": "new", "rent": 7000},
            {"emp_id": "EMP012", "name": "Divya Krishnan", "email": "divya.krishnan@company.com",
             "department": "Engineering", "designation": "QA Engineer", "grade": "L4",
             "location": "Bangalore", "city_tier": "metro", "joining_date": "2022-05-20",
             "manager_name": "Rajesh Nair", "manager_email": "rajesh.nair@company.com",
             "role": "employee", "annual_ctc": 900000, "pan": "LMPDK5678W",
             "bank": "7070808090", "regime": "new", "rent": 13000},
            {"emp_id": "EMP013", "name": "Rohan Desai", "email": "rohan.desai@company.com",
             "department": "Operations", "designation": "Logistics Coordinator", "grade": "L2",
             "location": "Ahmedabad", "city_tier": "non_metro", "joining_date": "2024-01-15",
             "manager_name": "Meera Joshi", "manager_email": "meera.joshi@company.com",
             "role": "employee", "annual_ctc": 550000, "pan": "MNPRD9012X",
             "bank": "9090101020", "regime": "new", "rent": 6000},
            {"emp_id": "EMP014", "name": "Neha Agarwal", "email": "neha.agarwal@company.com",
             "department": "HR", "designation": "VP Human Resources", "grade": "L8",
             "location": "Mumbai", "city_tier": "metro", "joining_date": "2016-01-10",
             "manager_name": None, "manager_email": None,
             "role": "admin", "annual_ctc": 2500000, "pan": "NOPNA3456Y",
             "bank": "2020303040", "regime": "new", "rent": 35000},
            {"emp_id": "EMP015", "name": "Suresh Pillai", "email": "suresh.pillai@company.com",
             "department": "Engineering", "designation": "DevOps Engineer", "grade": "L5",
             "location": "Bangalore", "city_tier": "metro", "joining_date": "2021-02-28",
             "manager_name": "Rajesh Nair", "manager_email": "rajesh.nair@company.com",
             "role": "employee", "annual_ctc": 1700000, "pan": "OPPSP7890Z",
             "bank": "4040505060", "regime": "new", "rent": 20000},
            {"emp_id": "EMP016", "name": "Pooja Mehta", "email": "pooja.mehta@company.com",
             "department": "Sales", "designation": "Business Analyst", "grade": "L4",
             "location": "Delhi", "city_tier": "metro", "joining_date": "2022-08-10",
             "manager_name": "Vikram Singh", "manager_email": "vikram.singh@company.com",
             "role": "employee", "annual_ctc": 1100000, "pan": "PQPPM1234A",
             "bank": "6060707080", "regime": "new", "rent": 14000},
            {"emp_id": "EMP017", "name": "Karthik Raman", "email": "karthik.raman@company.com",
             "department": "Finance", "designation": "Tax Analyst", "grade": "L5",
             "location": "Chennai", "city_tier": "metro", "joining_date": "2020-12-01",
             "manager_name": "Kavita Iyer", "manager_email": "kavita.iyer@company.com",
             "role": "employee", "annual_ctc": 1350000, "pan": "QRPKR5678B",
             "bank": "8080909010", "regime": "old", "rent": 16000},
            {"emp_id": "EMP018", "name": "Lakshmi Sundaram", "email": "lakshmi.sundaram@company.com",
             "department": "Operations", "designation": "Executive Assistant", "grade": "L2",
             "location": "Coimbatore", "city_tier": "non_metro", "joining_date": "2023-11-01",
             "manager_name": "Meera Joshi", "manager_email": "meera.joshi@company.com",
             "role": "employee", "annual_ctc": 480000, "pan": "RSPLS9012C",
             "bank": "1212343456", "regime": "new", "rent": 5000},
        ]

        emp_objects = []
        for e in employees_data:
            emp = Employee(
                emp_id=e["emp_id"], name=e["name"], email=e["email"],
                department=e["department"], designation=e["designation"], grade=e["grade"],
                location=e["location"], city_tier=e["city_tier"], joining_date=e["joining_date"],
                manager_name=e["manager_name"], manager_email=e["manager_email"],
                role=e["role"], password_hash=hash_password("password123"),
                annual_ctc=e["annual_ctc"], pan_number=e["pan"],
                bank_account=e["bank"], tax_regime=e["regime"],
                rent_paid_monthly=e["rent"],
            )
            db.add(emp)
            emp_objects.append((emp, e))

        db.commit()
        for emp, _ in emp_objects:
            db.refresh(emp)

        months = ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04"]
        lop_schedule = {
            3: {2: 2},     # Amit: 2 LOP in Feb
            9: {0: 1},     # Arjun: 1 LOP in Nov
            11: {4: 1},    # Sanjay: 1 LOP in Mar
            13: {1: 3},    # Rohan: 3 LOP in Dec
        }
        bonus_schedule = {
            0: {3: 15000},   # Rahul: bonus in Feb
            4: {3: 20000},   # Vikram: bonus in Feb
            6: {3: 25000},   # Rajesh: bonus in Feb
            9: {3: 18000},   # Kavita: bonus in Feb
            13: {5: 10000},  # Neha: bonus in Apr
        }
        arrears_schedule = {
            2: {4: 5000},    # Amit: arrears in Mar
            7: {5: 8000},    # Meera: arrears in Apr
        }

        for idx, (emp, edata) in enumerate(emp_objects):
            annual_ctc = edata["annual_ctc"]
            monthly_ctc = annual_ctc / 12

            basic_m = round(monthly_ctc * 0.40)
            hra_m = round(monthly_ctc * 0.20)
            da_m = round(monthly_ctc * 0.02)
            medical_m = 1250
            lta_m = round(monthly_ctc * 0.03)
            pf_employer_m = round(min(basic_m, 15000) * 0.12)
            remaining = round(monthly_ctc - basic_m - hra_m - da_m - medical_m - lta_m - pf_employer_m)
            special_m = max(0, remaining)

            gross_m = basic_m + hra_m + da_m + special_m + medical_m + lta_m
            pf_employee_m = round(min(basic_m, 15000) * 0.12)
            esic_employee_m = round(gross_m * 0.0075) if gross_m <= 21000 else 0
            esic_employer_m = round(gross_m * 0.0325) if gross_m <= 21000 else 0
            prof_tax_m = 200 if gross_m > 10000 else 0

            annual_gross = gross_m * 12
            tds_m = compute_monthly_tds_new_regime(annual_gross)

            for mi, month in enumerate(months):
                lop = lop_schedule.get(idx, {}).get(mi, 0)
                bonus = bonus_schedule.get(idx, {}).get(mi, 0)
                arrears = arrears_schedule.get(idx, {}).get(mi, 0)
                overtime = 0

                per_day = round((basic_m + da_m) / 22) if 22 > 0 else 0
                lop_deduction = lop * per_day

                month_gross = gross_m + bonus + arrears + overtime - lop_deduction
                month_deductions = pf_employee_m + esic_employee_m + prof_tax_m + tds_m + lop_deduction
                month_net = month_gross - (pf_employee_m + esic_employee_m + prof_tax_m + tds_m)

                record = SalaryRecord(
                    employee_id=emp.id, month=month,
                    ctc=round(monthly_ctc),
                    basic=basic_m, hra=hra_m, da=da_m,
                    special_allowance=special_m, medical=medical_m, lta=lta_m,
                    pf_employee=pf_employee_m, pf_employer=pf_employer_m,
                    esic_employee=esic_employee_m, esic_employer=esic_employer_m,
                    professional_tax=prof_tax_m, tds=tds_m,
                    lop_days=lop, lop_deduction=lop_deduction,
                    gross_pay=round(month_gross),
                    total_deductions=round(pf_employee_m + esic_employee_m + prof_tax_m + tds_m),
                    net_pay=round(month_net),
                    bonus=bonus, arrears=arrears, overtime=overtime,
                )
                db.add(record)

            leave = LeaveBalance(
                employee_id=emp.id,
                earned_leave=round(12 - (idx % 5) * 1.5, 1),
                sick_leave=round(6 - (idx % 3), 1),
                casual_leave=round(7 - (idx % 4), 1),
                maternity_leave=180 if idx in [1, 3, 5, 7, 9, 11, 15, 17] else 0,
                paternity_leave=15 if idx not in [1, 3, 5, 7, 9, 11, 15, 17] else 0,
                compensatory_off=idx % 3,
                lop_days_ytd=sum(lop_schedule.get(idx, {}).values()),
            )
            db.add(leave)

            for mi, month in enumerate(months):
                lop = lop_schedule.get(idx, {}).get(mi, 0)
                working = 22
                absent = lop
                present = working - absent
                att = AttendanceRecord(
                    employee_id=emp.id, month=month,
                    working_days=working, present_days=present,
                    absent_days=absent, lop_days=lop, half_days=0,
                )
                db.add(att)

        db.commit()

        disputes = [
            DisputeTicket(
                ticket_id="DSP-0001", employee_id=1, category="hra",
                description="My HRA deduction in March 2026 seems higher than usual. My rent has not changed but the deduction increased.",
                expected_amount=30000, actual_amount=28500, discrepancy_amount=1500,
                status="open", priority="medium",
                created_at=datetime(2026, 4, 5, 10, 30),
            ),
            DisputeTicket(
                ticket_id="DSP-0002", employee_id=3, category="salary",
                description="I had 2 LOP days in February but my salary deduction seems higher than expected for 2 days.",
                expected_amount=5700, actual_amount=7200, discrepancy_amount=-1500,
                status="in_review", priority="high",
                created_at=datetime(2026, 3, 10, 14, 15),
            ),
            DisputeTicket(
                ticket_id="DSP-0003", employee_id=5, category="bonus",
                description="My Q3 performance bonus was supposed to be ₹25,000 but I received ₹20,000. My manager confirmed the higher amount.",
                expected_amount=25000, actual_amount=20000, discrepancy_amount=5000,
                status="escalated", priority="high",
                created_at=datetime(2026, 3, 2, 9, 0),
            ),
            DisputeTicket(
                ticket_id="DSP-0101", employee_id=8, category="tds",
                description="TDS for 2026-03 looks higher after I switched declarations. Please review.",
                expected_amount=12500, actual_amount=14600, discrepancy_amount=-2100,
                status="awaiting_approval", priority="high",
                ai_reviewed=True, ai_verdict="escalated",
                ai_analysis="PEC flagged low confidence due to declaration mismatch; awaiting admin approval.",
                ai_reviewed_at=datetime(2026, 4, 12, 11, 45),
                created_at=datetime(2026, 4, 10, 16, 5),
            ),
            DisputeTicket(
                ticket_id="DSP-0102", employee_id=12, category="salary",
                description="Net pay for 2026-04 does not match deductions in payslip breakdown.",
                expected_amount=69000, actual_amount=65500, discrepancy_amount=3500,
                status="in_review", priority="medium",
                ai_reviewed=True, ai_verdict="resolved_invalid",
                ai_analysis="Deterministic check passed; discrepancy likely from misunderstanding of arrears timing.",
                ai_reviewed_at=datetime(2026, 4, 14, 9, 20),
                created_at=datetime(2026, 4, 13, 13, 30),
            ),
            DisputeTicket(
                ticket_id="DSP-0103", employee_id=16, category="bonus",
                description="Variable bonus promised as 18,000, credited as 12,000 in 2026-02.",
                expected_amount=18000, actual_amount=12000, discrepancy_amount=6000,
                status="escalated", priority="critical",
                ai_reviewed=True, ai_verdict="resolved_valid",
                ai_analysis="Discrepancy appears valid and above threshold; escalation required.",
                ai_reviewed_at=datetime(2026, 4, 15, 12, 10),
                created_at=datetime(2026, 4, 14, 8, 55),
            ),
        ]
        for d in disputes:
            db.add(d)

        policies = [
            PolicyDocument(
                title="Leave Policy FY 2025-26",
                category="Leave",
                content="""ACME CORPORATION - LEAVE POLICY (FY 2025-26)

1. TYPES OF LEAVE

1.1 Earned Leave (EL) / Privilege Leave
- Entitlement: 15 days per year (credited quarterly — 3.75 days per quarter)
- Accumulation: Can be carried forward up to a maximum of 45 days
- Encashment: Employees can encash up to 15 days of accumulated EL per year at basic salary rate
- Minimum: Must take at least 3 consecutive days for EL
- Approval: Requires manager approval at least 3 days in advance

1.2 Sick Leave (SL)
- Entitlement: 7 days per year
- Cannot be carried forward — lapses at year end
- Medical certificate required for SL of 3 or more consecutive days
- Can be taken in half-day increments
- No encashment allowed

1.3 Casual Leave (CL)
- Entitlement: 7 days per year
- Cannot be carried forward — lapses at year end
- Maximum 3 consecutive days at a time
- Cannot be combined with other leave types
- No encashment allowed

1.4 Maternity Leave
- Entitlement: 26 weeks (182 days) for first two children
- 12 weeks for third child onwards
- Fully paid leave
- Available from 8 weeks before expected delivery date
- Applicable to female employees who have worked for at least 80 days in the 12 months preceding delivery

1.5 Paternity Leave
- Entitlement: 15 days
- Must be taken within 6 months of child's birth
- Fully paid leave

1.6 Compensatory Off
- Granted for working on public holidays or weekends
- Must be availed within 30 days of accrual
- Requires manager approval

2. LOSS OF PAY (LOP)
- Applied when employee exhausts all available leave balances
- LOP deduction = (Basic + DA) / Working days in month × LOP days
- Affects PF contribution for that month
- More than 10 LOP days in a quarter triggers a review by HR

3. LEAVE ENCASHMENT
- Only Earned Leave can be encashed
- Maximum 15 days per year can be encashed
- Encashment amount = Basic salary per day × Number of days
- Encashment requests processed in January and July each year
- Full encashment of accumulated EL done at the time of separation

4. GENERAL RULES
- All leave requests must be submitted through the HRMS portal
- Unauthorized absence of 3+ consecutive days without intimation may lead to disciplinary action
- Leave balance is visible on the employee self-service portal
- Public holidays do not count as leave days
""",
                source_file="leave_policy_fy2025-26.pdf",
                uploaded_at=datetime(2025, 4, 1),
            ),
            PolicyDocument(
                title="HRA and Accommodation Policy",
                category="Compensation",
                content="""ACME CORPORATION - HRA & ACCOMMODATION POLICY

1. HOUSE RENT ALLOWANCE (HRA)

1.1 Eligibility
- All confirmed employees are eligible for HRA
- HRA is part of the CTC structure

1.2 HRA Amount
- Metro cities (Mumbai, Delhi, Bangalore, Chennai, Hyderabad, Kolkata): 50% of Basic Salary
- Non-metro cities: 40% of Basic Salary

1.3 HRA Tax Exemption
- HRA exemption under Section 10(13A) is the minimum of:
  (a) Actual HRA received
  (b) 50% of Basic (metro) or 40% of Basic (non-metro)
  (c) Rent paid minus 10% of Basic salary
- To claim exemption, employees must submit rent receipts quarterly
- Rent above ₹1,00,000 per month requires landlord PAN

1.4 Rent Receipt Submission
- Submit rent receipts quarterly through HRMS portal
- Deadline: 15th of the month following quarter end
- Late submissions may result in loss of exemption for that quarter

2. COMPANY ACCOMMODATION
- Senior management (L7+) may be offered company-provided accommodation
- Company accommodation is valued as a perquisite and taxed accordingly
- No HRA is payable when company accommodation is provided

3. RELOCATION SUPPORT
- Employees transferred to a different city receive:
  - One month's basic salary as relocation allowance
  - Temporary accommodation for up to 30 days
  - Moving expense reimbursement up to ₹50,000
""",
                source_file="hra_accommodation_policy.pdf",
                uploaded_at=datetime(2025, 4, 1),
            ),
            PolicyDocument(
                title="Variable Pay and Appraisal Policy",
                category="Compensation",
                content="""ACME CORPORATION - VARIABLE PAY & APPRAISAL POLICY

1. VARIABLE PAY STRUCTURE

1.1 Eligibility
- All confirmed employees from Grade L3 and above
- Pro-rated for employees joining mid-year

1.2 Variable Pay Components
- Individual Performance Bonus: 60% weightage
- Team/Department Performance: 25% weightage
- Company Performance: 15% weightage

1.3 Variable Pay Percentage (of Annual CTC)
- L2-L3: 5-8% of CTC
- L4-L5: 8-12% of CTC
- L6-L7: 12-18% of CTC
- L8+: 18-25% of CTC

1.4 Payout Schedule
- Variable pay is calculated annually after the appraisal cycle
- Payout in two installments: Q1 (60%) and Q3 (40%)
- Minimum 6 months of service required to be eligible

2. APPRAISAL CYCLE

2.1 Timeline
- Self-assessment submission: January 1-15
- Manager review: January 16-31
- Calibration meetings: February 1-15
- Final ratings communicated: February 28
- Increment effective: April 1

2.2 Rating Scale
- Outstanding (5): Exceeds all expectations, exceptional contribution
- Excellent (4): Frequently exceeds expectations
- Good (3): Meets all expectations consistently
- Needs Improvement (2): Partially meets expectations
- Unsatisfactory (1): Does not meet expectations

2.3 Increment Guidelines
- Outstanding: 15-20% increment
- Excellent: 10-15% increment
- Good: 7-10% increment
- Needs Improvement: 0-5% increment
- Unsatisfactory: No increment, placed on PIP

3. PERFORMANCE IMPROVEMENT PLAN (PIP)
- Duration: 90 days
- Clear objectives and milestones defined
- Bi-weekly check-ins with manager and HR
- Successful completion returns employee to normal cycle
- Failure to improve may result in separation
""",
                source_file="variable_pay_appraisal_policy.pdf",
                uploaded_at=datetime(2025, 4, 1),
            ),
            PolicyDocument(
                title="Reimbursement Policy",
                category="Benefits",
                content="""ACME CORPORATION - REIMBURSEMENT POLICY

1. TRAVEL REIMBURSEMENT

1.1 Local Travel
- Two-wheeler: ₹5 per km
- Four-wheeler: ₹12 per km
- Public transport: Actual fare with receipts
- Cab/auto: Actual fare, approved by manager

1.2 Outstation Travel
- Air travel: Economy class for L2-L5, Business class for L6+
- Train travel: AC 2-tier for L4+, AC 3-tier for L2-L3
- Hotel: Up to ₹3,000/night (non-metro), ₹5,000/night (metro) for L2-L5
- Hotel: Up to ₹8,000/night for L6+
- Daily allowance: ₹800 (non-metro), ₹1,200 (metro)

2. MEDICAL REIMBURSEMENT
- Annual limit: ₹15,000
- Covers: OPD expenses, medicines, diagnostic tests
- Submit original bills through HRMS within 30 days
- Family members covered: Self, spouse, dependent children, dependent parents

3. MOBILE REIMBURSEMENT
- L4+: Up to ₹1,000/month
- L6+: Up to ₹2,000/month
- Submit monthly bills through HRMS

4. WORK FROM HOME ALLOWANCE
- ₹1,500/month for employees in hybrid/remote mode
- Covers internet, electricity, and workspace setup
- Automatic credit — no reimbursement claim needed

5. GENERAL RULES
- All claims must be submitted within 30 days of expense
- Original receipts/invoices required for claims above ₹500
- False claims will result in disciplinary action
- Reimbursement processed within 15 working days of approval
""",
                source_file="reimbursement_policy.pdf",
                uploaded_at=datetime(2025, 4, 1),
            ),
            PolicyDocument(
                title="Code of Conduct and POSH Policy",
                category="Compliance",
                content="""ACME CORPORATION - CODE OF CONDUCT & POSH POLICY

1. CODE OF CONDUCT

1.1 Professional Behavior
- Treat all colleagues with respect and dignity
- Maintain professional conduct in all communications
- Protect company confidential information
- Avoid conflicts of interest
- Report any violations to HR or the Ethics Helpline

1.2 Attendance & Punctuality
- Standard working hours: 9:30 AM to 6:30 PM
- Flexible hours: Core hours 10:30 AM to 4:30 PM
- Inform manager of any absence before 10:00 AM
- Remote work requires prior manager approval

1.3 Data Protection
- Do not share login credentials
- Lock workstation when away from desk
- Report data breaches immediately to IT Security
- Follow clean desk policy

2. POSH POLICY (Prevention of Sexual Harassment)

2.1 Definition
- Sexual harassment includes unwelcome sexually determined behavior such as:
  physical contact, demand for sexual favors, sexually colored remarks,
  showing pornography, any other unwelcome physical/verbal/non-verbal conduct

2.2 Internal Complaints Committee (ICC)
- Presiding Officer: VP HR
- Committee meets within 7 days of receiving complaint
- Investigation completed within 90 days
- Confidentiality maintained throughout

2.3 Reporting
- Complaints can be filed via: ICC email, HRMS portal, or in person
- Written complaint required within 3 months of incident
- Anonymous complaints also investigated

2.4 Protection
- No retaliation against complainant
- Interim relief provided if needed
- Both parties treated fairly

3. GRIEVANCE REDRESSAL
- Step 1: Discuss with immediate manager
- Step 2: Raise ticket through HRMS grievance portal
- Step 3: HR investigates within 15 working days
- Step 4: Escalate to VP HR if unresolved
- Step 5: Final appeal to the Grievance Committee
""",
                source_file="code_of_conduct_posh.pdf",
                uploaded_at=datetime(2025, 4, 1),
            ),
        ]
        for p in policies:
            db.add(p)

        notifications = [
            Notification(
                employee_id=1, channel="in_app",
                subject="Dispute DSP-0001 status updated",
                body="Your dispute received a preliminary AI review and is currently in open state.",
                status="unread", sent_at=datetime(2026, 4, 16, 9, 5),
            ),
            Notification(
                employee_id=1, channel="in_app",
                subject="Payslip available for 2026-04",
                body="Your monthly payslip for April 2026 is now available.",
                status="read", sent_at=datetime(2026, 4, 16, 8, 30),
            ),
            Notification(
                employee_id=8, channel="in_app",
                subject="Approval pending for DSP-0101",
                body="Your dispute is waiting for admin approval due to high risk score.",
                status="unread", sent_at=datetime(2026, 4, 16, 10, 0),
            ),
            Notification(
                employee_id=14, channel="in_app",
                subject="3 high-risk approvals pending",
                body="Autonomy system detected SLA pressure in approval queue.",
                status="unread", sent_at=datetime(2026, 4, 16, 10, 5),
            ),
        ]
        for n in notifications:
            db.add(n)

        approval_requests = [
            HumanApprovalRequest(
                request_type="dispute_resolution",
                reference_id="DSP-0101",
                employee_id=8,
                reason="High-impact dispute outcome requires admin sign-off.",
                risk_score=0.82,
                proposed_action="Approve escalation and move ticket to final resolution workflow.",
                status="pending",
                requested_at=datetime(2026, 4, 12, 11, 50),
            ),
            HumanApprovalRequest(
                request_type="tax_recommendation",
                reference_id="2:2026-04",
                employee_id=2,
                reason="Autonomous tax recommendation generated for old-regime user.",
                risk_score=0.44,
                proposed_action="Recommend switching to new regime with estimated savings.",
                status="pending",
                requested_at=datetime(2026, 4, 16, 7, 30),
            ),
            HumanApprovalRequest(
                request_type="payroll_anomaly",
                reference_id="3:2026-03",
                employee_id=3,
                reason="Payroll consistency audit detected deduction mismatch.",
                risk_score=0.73,
                proposed_action="Re-validate salary record and decide correction path.",
                status="pending",
                requested_at=datetime(2026, 4, 16, 8, 10),
            ),
        ]
        for r in approval_requests:
            db.add(r)

        events = [
            AutonomousEvent(
                event_type="manual_run_job",
                payload_json='{"job_name":"tax_regime_advisor"}',
                status="processed",
                created_at=datetime(2026, 4, 16, 6, 0),
                processed_at=datetime(2026, 4, 16, 6, 0, 8),
            ),
            AutonomousEvent(
                event_type="recheck_payroll_audit",
                payload_json='{"reference_id":"3:2026-03"}',
                status="pending",
                created_at=datetime(2026, 4, 16, 10, 2),
            ),
            AutonomousEvent(
                event_type="job_failed",
                payload_json='{"job_name":"auto_dispute_review","error":"timeout"}',
                status="failed",
                created_at=datetime(2026, 4, 16, 5, 35),
                processed_at=datetime(2026, 4, 16, 5, 35, 5),
                error="Transient timeout while invoking external model.",
            ),
        ]
        for ev in events:
            db.add(ev)

        job_runs = [
            AutonomousJobRun(
                job_name="auto_dispute_review", status="success",
                summary="Auto-reviewed 3 disputes (2 escalated).",
                details_json='{"reviewed":3,"escalated":2}',
                started_at=datetime(2026, 4, 16, 6, 15),
                finished_at=datetime(2026, 4, 16, 6, 15, 11),
            ),
            AutonomousJobRun(
                job_name="payroll_consistency_audit", status="failed",
                summary="Database lock timeout while writing audit results.",
                details_json='{"error":"database is locked"}',
                started_at=datetime(2026, 4, 16, 7, 0),
                finished_at=datetime(2026, 4, 16, 7, 0, 9),
            ),
        ]
        for jr in job_runs:
            db.add(jr)

        sla_incidents = [
            SlaIncident(
                incident_type="sla_high_risk_approvals",
                severity="warning",
                summary="High-risk pending approvals exceeded SLA threshold.",
                details_json='{"high_risk_pending":3,"threshold":2}',
                status="open",
                created_at=datetime(2026, 4, 16, 8, 45),
            ),
            SlaIncident(
                incident_type="sla_failed_jobs",
                severity="critical",
                summary="Daily failed jobs exceeded SLA threshold.",
                details_json='{"failed_today":4,"threshold":2}',
                status="acknowledged",
                created_at=datetime(2026, 4, 16, 9, 0),
            ),
        ]
        for inc in sla_incidents:
            db.add(inc)

        db.commit()
        print("Database seeded successfully!")
        print(f"  - {len(employees_data)} employees created")
        print(f"  - {len(months)} months of salary records per employee")
        print(f"  - {len(disputes)} sample dispute tickets")
        print(f"  - {len(policies)} policy documents")
        print(f"  - {len(notifications)} sample notifications")
        print(f"  - {len(approval_requests)} pending approval requests")
        print(f"  - {len(events)} autonomy events")
        print(f"  - {len(sla_incidents)} SLA incidents")
        print()
        print("Default credentials:")
        print("  Employee:   rahul.sharma@company.com / password123")
        print("  HR Manager: priya.patel@company.com / password123")
        print("  Admin:      neha.agarwal@company.com / password123")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()  # Run: python seed_data.py from the backend folder
