# save as seed_claims.py
import json
from datetime import datetime
from main import app, db, FRAClaim
from pyproj import Transformer

# Transformer: UTM Zone 43N (EPSG:32643) -> WGS84 (EPSG:4326)
# Adjust if your coords are in a different zone
transformer = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)

# Load JSON data
with open("fra_records_with_coords.json", "r", encoding="utf-8") as f:
    claims_data = json.load(f)

def get_latlon(coords):
    """Convert UTM center_x/center_y to latitude and longitude."""
    if not coords or not isinstance(coords, list):
        return None, None
    coord = coords[0]
    if coord.get("center_x") is None or coord.get("center_y") is None:
        return None, None
    lon, lat = transformer.transform(coord["center_x"], coord["center_y"])
    return lat, lon

with app.app_context():
    inserted = 1
    for item in claims_data:
        lat, lon = get_latlon(item.get("Coordinates"))
        if lat is None or lon is None:
            continue  # skip claims with no valid coords

        claim = FRAClaim(
            holder_id = inserted,
            source_file=item.get("Letter_No_Date"),
            level= "dlc",
            address=item.get("Address"),
            village_details=item.get("Village_Details"),
            khasara_no=item.get("Khasra_No"),
            land_area=item.get("Land_Area"),
            purpose=item.get("Purpose"),
            caste_status=item.get("Caste_Status"),
            forest_block_name=item.get("Forest_Block_Name"),
            compartment_no=item.get("Compartment_No"),
            latitude=str(lat),   # store as string (your model uses String)
            longitude=str(lon),
            remark=item.get("Special_Remarks"),
            approved=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(claim)
        inserted += 1

    db.session.commit()
    print(f" Inserted {inserted} claims with valid lat/lon into FRAClaim table.")
