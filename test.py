import requests

BASE_URL = "http://127.0.0.1:5000"

# Register
res = requests.post(f"{BASE_URL}/register/dlc", json={
    "f_name": "John",
    "l_name": "Doe",
    "email": "dlc@example.com",
    "phone": "1234567890",
    "password": "secret"
})
print("Register status:", res.status_code)
print("Register raw:", res.text)  # 👈 show raw response
try:
    print("Register JSON:", res.json())
except Exception as e:
    print("Error parsing JSON:", e)

# Login
res = requests.post(f"{BASE_URL}/login/dlc", json={
    "email": "dlc@example.com",
    "password": "secret"
})
print("Login status:", res.status_code)
print("Login raw:", res.text)
try:
    token = res.json().get("access_token")
    print("Token:", token)
except Exception as e:
    print("Error parsing login JSON:", e)
    token = None

# Add claim (only if login worked)
if token:
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.post(f"{BASE_URL}/claims", json={
        "source_file": "file1.pdf",
        "holder_id": 1,
        "address": "Village A",
        "land_area": "2 acres"
    }, headers=headers)
    print("Add Claim status:", res.status_code)
    print("Add Claim raw:", res.text)

    # Fetch claims
    res = requests.get(f"{BASE_URL}/claims/all", headers=headers)
    print("Claims status:", res.status_code)
    print("Claims raw:", res.text)
