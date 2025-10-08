import requests

# URL of your Flask endpoint
url = "http://127.0.0.1:5000/claims"

# Dummy data for ClaimSource only
data = {
    "source_file": "uploads/source_docs/claim_dummy.pdf"
}

try:
    response = requests.post(url, json=data)
    response.raise_for_status()  # Raise an error for 4xx/5xx responses
    print("Response status:", response.status_code)
    print("Response JSON:", response.json())
except requests.exceptions.RequestException as e:
    print("Request failed:", e)
except ValueError:
    # This handles JSON decode errors
    print("Response is not valid JSON:", response.text)
