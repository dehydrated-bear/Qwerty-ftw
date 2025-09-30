# the data that we are using in this bitch 
#   the lulc data 
#   data from the person and his family etc 
#   land water /other bullshit
#   any other?


#i am gonna assume that krish is goona add the fra claim by the time i make this so i am jsut geeting the data from taht db

import requests
import sqlite3
from typing import Any, Dict, List
from pathlib import Path
import re


# Map LULC codes to meaningful names
LULC_CODE_MAP = {
    "l01": "Builtup, Urban",
    "l02": "Builtup, Rural",
    "l03": "Builtup, Mining",
    "l04": "Agriculture, Crop land",
    "l05": "Agriculture, Plantation",
    "l06": "Agriculture, Fallow",
    "l07": "Agriculture, Current Shifting Cultivation",
    "l08": "Forest, Evergreen / Semi evergreen",
    "l09": "Forest, Deciduous",
    "l10": "Forest, Forest Plantation",
    "l11": "Forest, Scrub Forest",
    "l12": "Forest, Swamp / Mangroves",
    "l13": "Grass/Grazing",
    "l14": "Barren / Salt Affected land",
    "l15": "Barren / Gullied / Ravinous Land",
    "l16": "Barren / Scrub land",
    "l17": "Barren / Sandy Area",
    "l18": "Barren / Barren Rocky",
    "l19": "Barren / Rann",
    "l20": "Wetlands, Inland Wetland",
    "l21": "Wetlands, Coastal Wetland",
    "l22": "Wetlands, River/Stream/Canals",
    "l23": "Wetlands, Reservoir/Lakes/Ponds",
    "l24": "Snow and Glacier",
}


def fetch_lulc_data(distcode: str, token: str, year: str = "1112") -> Dict[str, float]:
    """
    Fetch LULC data for given district.
    """
    url = f"https://bhuvan-app1.nrsc.gov.in/api/lulc/curljson.php?distcode={distcode}&year={year}&token={token}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Normalize values
        lulc_areas = {}
        for code in LULC_CODE_MAP.keys():
            val =host are online. data.get(code, "0")
            try:
                lulc_areas[code] = float(str(val).strip())
            except ValueError:
                lulc_areas[code] = 0.0
        return lulc_areas
    except Exception as e:
        print(f"[ERROR] LULC fetch failed: {e}")
        return {code: 0.0 for code in LULC_CODE_MAP.keys()}


def parse_land_area(area_str: str) -> float:
    """Convert '0.48 है.' → 0.48"""
    if not area_str:
        return 0.0
    match = re.search(r"[\d.]+", str(area_str))
    return float(match.group()) if match else 0.0


# hardcoded byatch as it is just bara baby

def get_claims_for_district(db_path: Path, district="बारां") -> List[Dict[str, Any]]:
    """
    Fetch FRA claims for a district (address or village_details match).
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    query = """
    SELECT id, holder_id, address, village_details, land_area, purpose, caste_status
    FROM fra_claims
    WHERE village_details LIKE ? OR address LIKE ?
    """
    cursor.execute(query, (f"%{district}%", f"%{district}%"))
    rows = cursor.fetchall()
    conn.close()

    claims = []
    for r in rows:
        claims.append({
            "id": r[0],
            "holder_id": r[1],
            "address": r[2],
            "village_details": r[3],
            "land_area": parse_land_area(r[4]),  # convert to float
            "purpose": (r[5] or "").replace("\n", "").strip(),
            "caste_status": (r[6] or "").replace("\n", "").strip(),
        })
    return claims

#checking the scheme for a one particular person , or instance

def check_scheme_eligibility(claim: Dict[str, Any], lulc_data: Dict[str, float]) -> Dict[str, bool]:
    eligibility = {
        "PM-KISAN": False,
        "Jal Jeevan Mission": False,
        "Van Dhan Yojana": False,
        "MGNREGA": False,
        "DAJGUA": False,
    }

    purpose = claim["purpose"].strip().lower()
    caste_status = claim["caste_status"].replace("\n", "").strip().lower()
    land_area = float(claim["land_area"]) if claim["land_area"] else 0.0

    # --- Environmental metrics ---
    water_percentage = lulc_data.get("l23", 0)  # Reservoir/Lakes/Ponds
    forest_cover_percentage = sum(lulc_data.get(code, 0) for code in ["l08", "l09", "l10", "l11"])
    soil_quality_percentage = 100 - lulc_data.get("l13", 0)  # (Dummy metric)

    # --- Rules ---
    if purpose in ["कृषि", "agriculture"] and land_area <= 2.0:
        eligibility["PM-KISAN"] = True

    if water_percentage < 50:
        eligibility["Jal Jeevan Mission"] = True

    if caste_status in ["st", "अनसूचित जनजाति", "scheduled tribe"] and forest_cover_percentage > 20:
        eligibility["Van Dhan Yojana"] = True

    if land_area < 1.0 and soil_quality_percentage < 60:
        eligibility["MGNREGA"] = True

    if purpose in ["कृषि", "डेयरी", "agriculture", "dairy"] and soil_quality_percentage > 70:
        eligibility["DAJGUA"] = True

    return eligibility


#for the summation of all the schems in a area 

def summarize_scheme_eligibility(db_path: Path, district: str, lulc_data: Dict[str, float]) -> Dict[str, int]:
    """
    Summarize how many claims in a district are eligible for each scheme.
    """
    claims = get_claims_for_district(db_path, district)

    summary = {
        "PM-KISAN": 0,
        "Jal Jeevan Mission": 0,
        "Van Dhan Yojana": 0,
        "MGNREGA": 0,
        "DAJGUA": 0,
        "total_claims": len(claims)
    }

    for claim in claims:
        eligibility = check_scheme_eligibility(claim, lulc_data)
        for scheme, is_eligible in eligibility.items():
            if is_eligible:  # scheme eligibility is True
                summary[scheme] += 1

    return summary



#function for the polygon mapping for the area and stuff

#!!!!!!!!! gives output in km square , not percentage

def get_aoi_lulc_stats(geom: str, token: str) -> Dict[str, Dict[str, Any]]:
    """
    Fetches LULC stats for an Area of Interest (AOI) from Bhuvan API
    and returns a clean, readable state-wise breakdown.
    
    Args:
        geom: WKT polygon string representing AOI.
        token: API token.
        
    Returns:
        Dictionary with state-wise LULC breakdown and mapped names.
    """
    url = "https://bhuvan-app1.nrsc.gov.in/api/lulc/curl_aoi.php"
    params = {"geom": geom, "token": token}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
    except Exception as e:
        return {"error": str(e)}

    raw_data = response.json()
    processed_data = {}

    for state_data in raw_data:
        state_name = state_data.get("State", "Unknown")
        processed_data[state_name] = {}

        for code, area in state_data.items():
            if code == "State":
                continue
            clean_code = code.replace("'", "").strip()  # Remove quotes from keys
            land_type = LULC_CODE_MAP.get(clean_code, clean_code)
            processed_data[state_name][land_type] = float(area)

    return processed_data



# --- Example usage ---
if __name__ == "__main__":
    DB_PATH = Path(__file__).parent / "instance" / "fra.db"
    TOKEN = "7f26fb328e484f3402d657e8f3e9b34e5696ce39"
    DISTRICT_CODE = "0831"  # Baran
    DISTRICT_NAME = "बारां"

    print("Fetching claims…")
    claims = get_claims_for_district(DB_PATH, DISTRICT_NAME)
    print(f"Total claims fetched: {len(claims)}")

    print("Fetching LULC data…")
    lulc_data = fetch_lulc_data(DISTRICT_CODE, TOKEN)

    print("Summarizing scheme eligibility…")
    summary = summarize_scheme_eligibility(DB_PATH, DISTRICT_NAME, lulc_data)

    print("\n📊 District Eligibility Summary:")
    for scheme, count in summary.items():
        print(f"{scheme}: {count}")

    

    for claim in claims:
        eligibility = check_scheme_eligibility(claim, lulc_data)
        print(f"\n📄 Claim ID: {claim['id']} | Holder: {claim['holder_id']}")
        print("Purpose:", claim["purpose"], "| Caste:", claim["caste_status"], "| Land:", claim["land_area"])
        print("Scheme Eligibility:", eligibility)



    token1 = "b142ff539f1f037ade84f273ce12b61aaf669b5b"

    geom_example = "POLYGON((77.537826049804 18.312927062987,77.539885986327 18.279624755858,77.596190917968 18.295417602538,77.537826049804 18.312927062987))"

    result = get_aoi_lulc_stats(geom_example, token1)
    from pprint import pprint
    pprint(result)


