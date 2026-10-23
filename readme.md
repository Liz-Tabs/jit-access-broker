# Just-In-Time (JIT) Ephemeral Access Broker

An end-to-end Zero-Trust Ephemeral Access Broker built with **Python 3.13**, **FastAPI**, and **Pydantic**. This system automates identity claim parsing, enforces least-privilege security policies, issues short-lived simulated AWS STS credentials, and maintains a persistent JSON audit trail.

---

## 🏗 System Architecture & Implemented Features

* **Automated OIDC Authentication Flow:** Built a CLI client with an embedded local loopback HTTP server running on port `8090` to handle OIDC callback redirects cleanly without port contention.
* **Dynamic Client-Side Identity Claims Parsing:** Integrated `PyJWT` to decode local JWT payloads and extract user identity claims automatically, eliminating hardcoded user inputs.
* **FastAPI Policy & Security Engine:** Engineered a backend validation engine enforcing strict security controls:
  * **`401 Unauthorized`:** Blocks requests with invalid, missing, or expired tokens.
  * **`403 Forbidden`:** Rejects non-compliant requests (e.g., production access requests with justifications under 10 characters).
  * **`200 OK`:** Dynamically issues temporary simulated AWS STS credentials upon successful token and policy validation.
* **Persistent Audit Trail:** Built an automated logger that records every security decision (`APPROVED`, `DENIED_AUTH`, `DENIED_POLICY`) with ISO UTC timestamps into a structured `audit_log.json` file.

---

## 📁 Repository Structure

```text
jit-access-broker/
├── broker/
│   └── main.py          # FastAPI backend, policy enforcement & persistent audit logging
├── cli/
│   └── client.py        # CLI client, OIDC loopback server (port 8090) & PyJWT claim parsing
├── audit_log.json       # Generated immutable event audit trail
└── README.md
```

---

## 🛠 Tech Stack

* **Language:** Python 3.13
* **Backend Framework:** FastAPI, Uvicorn, Pydantic
* **Authentication & JWT Parsing:** PyJWT
* **Networking & HTTP:** Python Standard Library (`http.server`, `urllib`, `webbrowser`), Requests
* **Platform:** Ubuntu Linux

---

## 🚀 Execution & Verification

### 1. Start the FastAPI Backend
```bash
uvicorn broker.main:app --reload
```
*(Interactive API documentation is accessible at `http://127.0.0.1:8000/docs`)*

### 2. Run the CLI Client
```bash
python3 -m cli.client
```

### 3. Review Persistent Audit Logs
Inspect the generated `audit_log.json` file to verify structured security logs:
```json
{
  "timestamp": "2026-10-23T10:15:30.123456+00:00",
  "status": "APPROVED",
  "user_email": "alice.dev@company.com",
  "target_environment": "aws-production",
  "details": "Temporary Zero-Trust credentials generated successfully."
}
```