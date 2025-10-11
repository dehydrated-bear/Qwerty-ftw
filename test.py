import requests

BASE_URL = "http://127.0.0.1:5000/lgeom"  # or your deployed URL

# ---------- TEST GET ----------
params = {
    "x": 78.1234,
    "y": 23.5678,
    "srs": "EPSG:32643",
    "buffer_size": 500
}

print("Testing GET /lgeom ...")
response = requests.get(BASE_URL, params=params)
print("Status:", response.status_code)
print("Response:", response.json())


# ---------- TEST POST ----------
payload = {
    "x": 78.1234,
    "y": 23.5678,
    "srs": "EPSG:32643",
    "buffer_size": 500
}

print("\nTesting POST /lgeom ...")
response = requests.post(BASE_URL, json=payload)
print("Status:", response.status_code)
print("Response:", response.json())
