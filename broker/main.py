from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
import json
from datetime import datetime, timezone

app = FastAPI(title="JIT Access Broker API", version="1.0.0")

@app.get("/")
async def root():
    return {
        "message": "Welcome to the JIT Access Broker API",
        "interactive_docs": "http://127.0.0.1:8000/docs"
    }

class AccessRequest(BaseModel):
    user_email: EmailStr
    idp_token: str
    target_environment: str
    requested_role: str
    duration_seconds: int = 1800  # Default 30 minutes
    justification: str

def write_audit_log(status_str: str, email: str, target: str, reason: str):
    """Appends an immutable audit record to a local JSON file."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status_str,
        "user_email": email,
        "target_environment": target,
        "details": reason
    }
    with open("audit_log.json", "a") as log_file:
        log_file.write(json.dumps(log_entry) + "\n")

@app.post("/request-access")
async def request_access(payload: AccessRequest):
    """
    Receives an access request, validates identity & policy, 
    and simulates generating short-lived AWS STS credentials.
    """
    
    if not payload.idp_token.startswith("mock_jwt_token"):
        write_audit_log("DENIED_AUTH", payload.user_email, payload.target_environment, "Invalid or expired OIDC token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OIDC token."
        )
    
    if "production" in payload.target_environment.lower() and len(payload.justification) < 10:
        write_audit_log("DENIED_POLICY", payload.user_email, payload.target_environment, "Justification too short for production access.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Policy violation: Production access requires a detailed justification (at least 10 characters)."
        )

    simulated_credentials = {
        "AccessKeyId": "ASIA_MOCK_ACCESS_KEY_98765",
        "SecretAccessKey": "mock_secret_key_secure_xyz",
        "SessionToken": "mock_session_token_abc123",
        "ExpiresInSeconds": payload.duration_seconds
    }

    write_audit_log("APPROVED", payload.user_email, payload.target_environment, "Temporary Zero-Trust credentials generated successfully.")
    print(f"[AUDIT] Access APPROVED for {payload.user_email} to {payload.target_environment} (Duration: {payload.duration_seconds}s)")

    return {
        "status": "APPROVED",
        "message": "Temporary Zero-Trust credentials generated successfully.",
        "target_environment": payload.target_environment,
        "assumed_role": payload.requested_role,
        "credentials": simulated_credentials
    }