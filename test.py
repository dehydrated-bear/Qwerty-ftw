import unittest
from main import app

class AOILULCTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Login to get JWT token
        login_resp = self.app.post("/login/dlc", json={
            "email": "testuser@example.com",
            "password": "password123"
        })
        self.token = login_resp.get_json().get("access_token")
        self.assertIsNotNone(self.token, "JWT token not received from login")

    def test_aoi_lulc_endpoint(self):
        geom_example = (
            "POLYGON((77.537826049804 18.312927062987,"
            "77.539885986327 18.279624755858,"
            "77.596190917968 18.295417602538,"
            "77.537826049804 18.312927062987))"
        )

        resp = self.app.post(
            "/lulc/aoi",
            json={"geom": geom_example},
            headers={"Authorization": f"Bearer {self.token}"}
        )

        print("Status code:", resp.status_code)
        try:
            print("Response JSON:", resp.get_json())
        except Exception as e:
            print("Failed to decode JSON:", e)
            print("Raw response data:", resp.data.decode())

        self.assertEqual(resp.status_code, 200, f"Unexpected status code: {resp.status_code}")

        data = resp.get_json()
        self.assertIsInstance(data, dict, "Response should be a dictionary")
        if data and "error" not in data:
            for state_name, lulc_info in data.items():
                self.assertIsInstance(lulc_info, dict, f"LULC info for {state_name} is not a dict")
                for land_type, area in lulc_info.items():
                    self.assertIsInstance(area, (int, float), f"Area for {land_type} is not numeric")


if __name__ == "__main__":
    unittest.main()
