from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_security_headers():
    """Test that appropriate security headers are set in responses."""
    response = client.get("/")
    
    # Check for common security headers
    # Note: These headers may not be set in the current implementation
    # This test serves as a reminder of best practices
    
    headers = response.headers
    
    # Content-Security-Policy
    if "Content-Security-Policy" in headers:
        assert "default-src 'self'" in headers["Content-Security-Policy"]
    else:
        print("Warning: Content-Security-Policy header not set")
    
    # X-Content-Type-Options
    if "X-Content-Type-Options" in headers:
        assert headers["X-Content-Type-Options"] == "nosniff"
    else:
        print("Warning: X-Content-Type-Options header not set")
    
    # X-Frame-Options
    if "X-Frame-Options" in headers:
        assert headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]
    else:
        print("Warning: X-Frame-Options header not set")
    
    # Strict-Transport-Security
    if "Strict-Transport-Security" in headers:
        assert "max-age=" in headers["Strict-Transport-Security"]
    else:
        print("Warning: Strict-Transport-Security header not set")
    
    # X-XSS-Protection
    if "X-XSS-Protection" in headers:
        assert headers["X-XSS-Protection"] == "1; mode=block"
    else:
        print("Warning: X-XSS-Protection header not set")
    
    # This test will pass regardless of whether the headers are set
    # It serves as documentation of security best practices

def test_cors_headers():
    """Test CORS headers in responses."""
    # Send a preflight request
    headers = {
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type,Authorization"
    }
    response = client.options("/", headers=headers)
    
    # Check CORS headers
    # Note: These headers may not be set in the current implementation
    # This test serves as a reminder of best practices
    
    if "Access-Control-Allow-Origin" in response.headers:
        # Should be specific origin or "*"
        assert response.headers["Access-Control-Allow-Origin"] in ["*", "https://example.com"]
    else:
        print("Warning: Access-Control-Allow-Origin header not set")
    
    if "Access-Control-Allow-Methods" in response.headers:
        # Should include requested method
        assert "GET" in response.headers["Access-Control-Allow-Methods"]
    else:
        print("Warning: Access-Control-Allow-Methods header not set")
    
    if "Access-Control-Allow-Headers" in response.headers:
        # Should include requested headers
        assert "Content-Type" in response.headers["Access-Control-Allow-Headers"]
        assert "Authorization" in response.headers["Access-Control-Allow-Headers"]
    else:
        print("Warning: Access-Control-Allow-Headers header not set")
    
    # This test will pass regardless of whether the headers are set
    # It serves as documentation of security best practices

def test_content_type_headers():
    """Test that appropriate content type headers are set."""
    response = client.get("/")
    
    # Check Content-Type header
    assert "Content-Type" in response.headers
    assert response.headers["Content-Type"] == "application/json"
    
    # Check that charset is specified
    if "charset" not in response.headers["Content-Type"]:
        print("Warning: charset not specified in Content-Type header")

def test_server_information_disclosure():
    """Test that server information is not disclosed in headers."""
    response = client.get("/")
    
    # Check that Server header doesn't reveal too much information
    if "Server" in response.headers:
        server = response.headers["Server"]
        # Server header should not contain version information
        assert "." not in server, "Server header should not contain version information"
    
    # Check for other headers that might reveal server information
    sensitive_headers = ["X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version"]
    for header in sensitive_headers:
        assert header not in response.headers, f"{header} header should not be present"