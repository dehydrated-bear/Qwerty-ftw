# save as seed_claims.py
import json
from datetime import datetime
from main import app, db, FRAClaim  # make sure your Flask app file is named app.py

# Load JSON data
with open("fra_records_with_coords.json", "r", encoding="utf-8") as f:
    claims_data = json.load(f)

def has_valid_coordinates(coords):
    """Check if coordinates exist and contain numeric values."""
    if not coords or not isinstance(coords, list):
        return False
    coord = coords[0]  # assuming only one per claim
    return coord.get("center_x") is not None and coord.get("center_y") is not None

with app.app_context():
    inserted = 0
    for item in claims_data:
        if not has_valid_coordinates(item.get("Coordinates")):
            continue  # skip if no valid coords

        claim = FRAClaim(
            source_file=item.get("Letter_No_Date"),
            holder_id=None,  # adjust if you have a mapping
            address=item.get("Address"),
            village_details=item.get("Village_Details"),
            khasara_no=item.get("Khasra_No"),
            land_area=item.get("Land_Area"),
            purpose=item.get("Purpose"),
            caste_status=item.get("Caste_Status"),
            forest_block_name=item.get("Forest_Block_Name"),
            compartment_no=item.get("Compartment_No"),
            gps_addr=item.get("GPS_Address"),
            remark=item.get("Special_Remarks"),
            level=None,
            approved=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(claim)
        inserted += 1

    db.session.commit()
    print(f"✅ Inserted {inserted} claims with valid coordinates into FRAClaim table.")
