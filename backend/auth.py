"""
Authentication helpers: password hashing (bcrypt), JWT create/decode, and FastAPI dependencies.

`get_current_user` reads the Bearer token, validates it, and loads the employee from the DB.
`require_role` builds a dependency that only allows certain roles (HR/admin).
"""
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt as _bcrypt
from database import get_db, SessionLocal
from models import Employee
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS

security = HTTPBearer()


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = _bcrypt.gensalt()
    return _bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    employee_id = payload.get("employee_id")
    if employee_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=401, detail="User not found")
        return {
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
            "rent_paid_monthly": employee.rent_paid_monthly,
        }
    finally:
        db.close()


def require_role(allowed_roles: list):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
