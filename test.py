import requests

# --- Step 1: Upload a document ---
upload_url = "http://localhost:8000/upload"
file_path = "hive.pdf"  # must exist locally

with open(file_path, "rb") as f:
    files = {"file": (file_path, f, "application/pdf")}
    response = requests.post(upload_url, files=files)
print("Status code:", response.status_code)
print("Response text:", response.text)
print("Upload status:", response.status_code)
print("Upload response:", response.json())

if response.status_code != 201:
    exit()
claim_id = response.json().get("claim_id")

# --- Step 2: Get all uploaded files for that claim ---
get_url = f"http://localhost:8000/uploads/{claim_id}"
get_resp = requests.get(get_url)

print("\nList status:", get_resp.status_code)
print("List response:", get_resp.json())
