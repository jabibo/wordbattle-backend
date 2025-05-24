import requests
import json

# API endpoint
url = "http://localhost:8000/users/register"

# User data
user_data = {
    "username": "testuser",
    "password": "testpassword"
}

# Send POST request
headers = {"Content-Type": "application/json"}
response = requests.post(url, data=json.dumps(user_data), headers=headers)

# Print response
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
