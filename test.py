import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# --- Step 1: Login ---
login_data = {
    "email": "testuser@example.com",  # Replace with your test user
    "password": "password123"
}

r = requests.post(f"{BASE_URL}/login/dlc", json=login_data)
if r.status_code != 200:
    raise Exception(f"Login failed: {r.status_code} {r.text}")

token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# --- Step 2: Fetch all claims to get latest claim ID ---
r = requests.get(f"{BASE_URL}/claims/all", headers=headers)
if r.status_code != 200:
    raise Exception(f"Failed to fetch claims: {r.status_code} {r.text}")

try:
    claims = r.json()
except Exception:
    print("Response is not valid JSON. Raw response:")
    print(r.text)
    claims = []

if not claims:
    raise Exception("No claims found. Add a claim first.")

# Use the latest claim
claim_id = claims[-1]["id"]

# --- Step 3: Fetch Claim Eligibility ---
district = "बारां"
distcode = "0831"

r = requests.get(
    f"{BASE_URL}/eligibility/{claim_id}?district={district}&distcode={distcode}",
    headers=headers
)

print(f"\nStatus Code: {r.status_code}")

try:
    data = r.json()
    print("Claim Eligibility:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception:
    print("Response is not valid JSON. Raw response:")
    print(r.text)
