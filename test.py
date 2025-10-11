import requests

BASE_URL = "http://127.0.0.1:5000/lgeom"  # or your deployed URL

# ---------- TEST GET ----------
params = {
  "x": 663307.8837934907,
  "y": 2740180.604520008,
  "srs": "EPSG:32643",
  "buffer_size": 500
}
print("Testing GET /lgeom ...")
response = requests.get(BASE_URL, params=params)
print("Status:", response.status_code)
print("Response:", response.json())


# ---------- TEST POST ----------
payload = {
    "x": 76.5110,
    "y": 25.1000,
    "srs": "EPSG:32643",
    "buffer_size": 500
}

print("\nTesting POST /lgeom ...")
response = requests.post(BASE_URL, json=payload)
print("Status:", response.status_code)
print("Response:", response.json())
