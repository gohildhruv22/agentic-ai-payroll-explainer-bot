"""
SQLAlchemy ORM models — one class per database table.

Defines employees, salary rows, leave/attendance, disputes, policies, audit logs, chat messages,
and in-app notifications. Used by routes and seed_data to read/write SQLite (or other DB URL).
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy import ForeignKey
from datetime import datetime
from database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    department = Column(String(50), nullable=False)
    designation = Column(String(100), nullable=False)
    grade = Column(String(10), nullable=False)
    location = Column(String(50), nullable=False)
    city_tier = Column(String(10), nullable=False, default="metro")
    joining_date = Column(String(20), nullable=False)
    manager_name = Column(String(100), nullable=True)
    manager_email = Column(String(150), nullable=True)
    role = Column(String(20), nullable=False, default="employee")
    password_hash = Column(String(200), nullable=False)
    annual_ctc = Column(Float, nullable=False, default=0)
    pan_number = Column(String(20), nullable=True)
    bank_account = Column(String(30), nullable=True)
    tax_regime = Column(String(10), nullable=False, default="new")
    rent_paid_monthly = Column(Float, nullable=False, default=0)


class SalaryRecord(Base):
    __tablename__ = "salary_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True)
    ctc = Column(Float, nullable=False)
    basic = Column(Float, nullable=False)
    hra = Column(Float, nullable=False)
    da = Column(Float, nullable=False, default=0)
    special_allowance = Column(Float, nullable=False, default=0)
    medical = Column(Float, nullable=False, default=0)
    lta = Column(Float, nullable=False, default=0)
    pf_employee = Column(Float, nullable=False, default=0)
    pf_employer = Column(Float, nullable=False, default=0)
    esic_employee = Column(Float, nullable=False, default=0)
    esic_employer = Column(Float, nullable=False, default=0)
    professional_tax = Column(Float, nullable=False, default=0)
    tds = Column(Float, nullable=False, default=0)
    lop_days = Column(Integer, nullable=False, default=0)
    lop_deduction = Column(Float, nullable=False, default=0)
    gross_pay = Column(Float, nullable=False)
    total_deductions = Column(Float, nullable=False)
    net_pay = Column(Float, nullable=False)
    bonus = Column(Float, nullable=False, default=0)
    arrears = Column(Float, nullable=False, default=0)
    overtime = Column(Float, nullable=False, default=0)


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    earned_leave = Column(Float, nullable=False, default=0)
    sick_leave = Column(Float, nullable=False, default=0)
    casual_leave = Column(Float, nullable=False, default=0)
    maternity_leave = Column(Float, nullable=False, default=0)
    paternity_leave = Column(Float, nullable=False, default=0)
    compensatory_off = Column(Float, nullable=False, default=0)
    lop_days_ytd = Column(Float, nullable=False, default=0)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True)
    working_days = Column(Integer, nullable=False, default=22)
    present_days = Column(Integer, nullable=False, default=22)
    absent_days = Column(Integer, nullable=False, default=0)
    lop_days = Column(Integer, nullable=False, default=0)
    half_days = Column(Integer, nullable=False, default=0)


class DisputeTicket(Base):
    __tablename__ = "dispute_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(20), unique=True, index=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    expected_amount = Column(Float, nullable=True)
    actual_amount = Column(Float, nullable=True)
    discrepancy_amount = Column(Float, nullable=True)
    evidence_json = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="open")
    priority = Column(String(20), nullable=False, default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    # AI Review fields
    ai_reviewed = Column(Boolean, default=False)
    ai_verdict = Column(String(30), nullable=True)  # resolved_valid, resolved_invalid, escalated
    ai_analysis = Column(Text, nullable=True)
    ai_reviewed_at = Column(DateTime, nullable=True)
    admin_reviewed = Column(Boolean, default=False)
    admin_action = Column(String(30), nullable=True)  # approved, rejected, modified
    admin_notes = Column(Text, nullable=True)
    admin_reviewed_at = Column(DateTime, nullable=True)


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    embedding_json = Column(Text, nullable=True)
    source_file = Column(String(200), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, nullable=True)
    query_text = Column(Text, nullable=True)
    intent = Column(String(50), nullable=True)
    agent_used = Column(String(50), nullable=True)
    tools_called_json = Column(Text, nullable=True)
    response_summary = Column(Text, nullable=True)
    escalation_triggered = Column(Boolean, default=False)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    channel = Column(String(20), nullable=False, default="in_app")
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="sent")
    sent_at = Column(DateTime, default=datetime.utcnow)


class AutonomousJobRun(Base):
    __tablename__ = "autonomous_job_runs"

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(80), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="success")
    summary = Column(Text, nullable=True)
    details_json = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    finished_at = Column(DateTime, nullable=True)


class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    memory_type = Column(String(50), nullable=False, default="preference")
    key = Column(String(100), nullable=False, index=True)
    value = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.5)
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)


class HumanApprovalRequest(Base):
    __tablename__ = "human_approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String(50), nullable=False, index=True, default="dispute_resolution")
    reference_id = Column(String(50), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    risk_score = Column(Float, nullable=False, default=0)
    proposed_action = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected
    requested_at = Column(DateTime, default=datetime.utcnow, index=True)
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)


class AutonomousEvent(Base):
    __tablename__ = "autonomous_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(80), nullable=False, index=True)
    payload_json = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, processed, failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)


class SlaIncident(Base):
    __tablename__ = "sla_incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String(80), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="warning")
    summary = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="open")  # open, acknowledged, resolved
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)
