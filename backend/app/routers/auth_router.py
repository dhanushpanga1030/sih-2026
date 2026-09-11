"""Auth routes — login, token verification, RBAC.

No database dependency — uses hardcoded demo users for hackathon demo.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

router = APIRouter()

SECRET_KEY = "safehabitat-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

security = HTTPBearer(auto_error=False)

# Demo users — role matches spatial_models.UserRole values
DEMO_USERS = {
    "admin": {"password": "admin123", "role": "admin", "email": "admin@safehabitat.gov.in"},
    "district_officer": {
        "password": "district123",
        "role": "district_officer",
        "email": "district@safehabitat.gov.in",
    },
    "analyst": {
        "password": "analyst123",
        "role": "village_analyst",
        "email": "analyst@safehabitat.gov.in",
    },
}


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Extract user from JWT. Returns dict with username + role."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"username": username, "role": role}


def require_role(*allowed_roles: str):
    """Dependency factory — rejects if user role not in allowed_roles."""

    def checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403, detail=f"Requires role: {', '.join(allowed_roles)}"
            )
        return user

    return checker


@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(body: LoginRequest):
    """Authenticate with demo credentials and receive a JWT token."""
    user = DEMO_USERS.get(body.username)
    if not user or user["password"] != body.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": body.username, "role": user["role"]})
    return TokenResponse(
        access_token=token,
        role=user["role"],
        username=body.username,
    )


@router.get("/auth/me", tags=["Auth"])
def whoami(user: dict = Depends(get_current_user)):
    """Return the current authenticated user."""
    return user
