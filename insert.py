import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("instance/fra.db")


#for inserting 2 sample datat to test this shit out

sample_data = [
    (
        None,                       # id (autoincrement, can be None)
        None,                       # source_file (optional)
        1,                          # holder_id (set a dummy id)
        "ग्राम बमोरी तह.अटरू\nजि. बारा",  # address
        "ग्रा. बमोरी\nप . बमोरीतह. तह.\nअ टरू\nजि. बारां", # village_details
        "268",                      # khasara_no
        "0.48",                     # land_area
        "कृषि",                    # purpose
        "अनसूचित\nजनजाति",         # caste_status
        "बीड घास\nबमेारी",          # forest_block_name
        "अटरू",                    # compartment_no
        "",                         # gps_addr
        "",                         # level
        "",                         # remark
        False,                      # approved
        datetime.utcnow(),          # created_at
        datetime.utcnow()           # updated_at
    ),
    (
        None,
        None,
        2,
        "ग्राम कुकर तालाब\nपं. कु.डी तह.\nअटरू जि. बारां",
        "ग्राम ककरतालाब\nपं. कु.डी तह.\nअटरू जि. बारां",
        "1889",
        "0.48",
        "कृषि",
        "अनसूचित\nजनजाति",
        "कु.डी",
        "अटरू",
        "",
        "",
        "",                         # Add this missing comma here
        False,
        datetime.utcnow(),
        datetime.utcnow()
    ),
]


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

insert_query = """
    INSERT INTO fra_claims (
        id, source_file, holder_id, address, village_details, khasara_no,
        land_area, purpose, caste_status, forest_block_name, compartment_no,
        gps_addr, level, remark, approved, created_at, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

cursor.executemany(insert_query, sample_data)
conn.commit()
conn.close()

print("Inserted sample claims into fra_claims table.")
