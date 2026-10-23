import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import sys
import requests
import json
import jwt  


captured_token = None

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

class OIDCCallbackHandler(BaseHTTPRequestHandler):
    """Handles the redirect callback from the Identity Provider."""
    
    def do_GET(self):
        global captured_token
        
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        if "token" in query_params:
            captured_token = query_params["token"][0]
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authentication Successful!</h1><p>You can close this tab and return to your terminal.</p>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h1>Authentication Failed!</h1><p>No token found in response.</p>")

    def log_message(self, format, *args):
        return

def authenticate_user() -> str:
    """Spins up a temporary local server on port 8090 and triggers the login flow."""
    server_address = ('', 8090)
    httpd = ReusableHTTPServer(server_address, OIDCCallbackHandler)
    
    mock_idp_url = "http://127.0.0.1:8090/callback?token=mock_jwt_token_alice_dev"
    
    print("\n--- Zero-Trust Authentication ---")
    print("Opening your browser to log in via OIDC...")
    
    webbrowser.open(mock_idp_url)
    
    httpd.handle_request()
    httpd.server_close()
    
    if captured_token:
        print("✓ Identity verified successfully!")
        return captured_token
    else:
        print("✗ Authentication failed.")
        sys.exit(1)

def request_jit_access(token: str):
    """Extracts identity from the OIDC token and sends the access request to the FastAPI backend."""
    print("\n--- Zero-Trust JIT Access Request ---")
    
    try:
        claims = jwt.decode(token, options={"verify_signature": False})
        extracted_email = claims.get("sub", "alice.dev@company.com")
    except Exception:
        extracted_email = "alice.dev@company.com"
        
    print(f"✓ Authenticated as: {extracted_email}")
    
    target_env = input("Target environment [aws-production]: ").strip() or "aws-production"
    role = input("Requested IAM Role ARN [arn:aws:iam::123456789012:role/JIT-Engineer]: ").strip() or "arn:aws:iam::123456789012:role/JIT-Engineer"
    justification = input("Business justification (min 10 chars) [Investigating payment latency incident INC-8821]: ").strip() or "Investigating payment latency incident INC-8821"
    
    payload = {
        "user_email": extracted_email,
        "idp_token": token,
        "target_environment": target_env,
        "requested_role": role,
        "duration_seconds": 1800,
        "justification": justification
    }
    
    print("\nSubmitting request to JIT Access Broker API...")
    
    try:
        response = requests.post("http://127.0.0.1:8000/request-access", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n==============================================")
            print("🚀 ACCESS GRANTED!")
            print("==============================================")
            print(f"Target: {data['target_environment']}")
            print(f"Role:   {data['assumed_role']}")
            print("\nTemporary Credentials Generated:")
            print(json.dumps(data['credentials'], indent=2))
            print("==============================================")
        else:
            print(f"\n❌ Access Denied ({response.status_code}):")
            print(response.json().get("detail", response.text))
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the JIT Broker API. Is your Uvicorn server running on port 8000?")

if __name__ == "__main__":
    token = authenticate_user()
    request_jit_access(token)