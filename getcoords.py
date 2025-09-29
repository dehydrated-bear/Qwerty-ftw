import pandas as pd
import re
import json
import requests
from time import sleep
from fuzzywuzzy import fuzz

# ---------------------------
# 1️⃣ Load CSV
# ---------------------------
csv_path = "baran_location_hierarchy.csv"
print(f"📂 Loading CSV: {csv_path}")
df = pd.read_csv(csv_path)

# Strip column names
df.columns = df.columns.str.strip()
print(f"✅ Columns after strip: {df.columns.tolist()}")

# Columns for combined string
name_cols = ["District_Name", "Tehsil_Name", "RI_Name", "Halka_Name", "Village_Name"]
id_cols = ["District_ID", "Tehsil_ID", "RI_ID", "Halka_ID", "Village_ID"]

# ---------------------------
# 2️⃣ Preprocess rows
# ---------------------------
def preprocess_row(row):
    combined = " ".join(str(row[col]).strip() for col in name_cols)
    if combined.strip().lower().endswith("digitized"):
        return None
    return combined

df['combined_str'] = df.apply(preprocess_row, axis=1)
df = df[df['combined_str'].notna()]
print(f"✅ Rows after preprocessing: {len(df)}")

# ---------------------------
# 3️⃣ Bhunaksha URL generator
# ---------------------------
def generate_bhunaksha_url(row, plot_no):
    try:
        numbers = [
            str(row["District_ID"]),
            str(row["Tehsil_ID"]).zfill(3),
            str(row["RI_ID"]),
            str(int(row["Halka_ID"])).zfill(5),
            str(row["Village_ID"])
        ]
        unique_numbers = numbers + ["001"]
        levels_str = ",".join(unique_numbers) + ","
        levels_encoded = levels_str.replace(",", "%2C")
        url = f"https://bhunaksha.rajasthan.gov.in/Viewmap/ScalarDatahandler?OP=5&state=08&levels={levels_encoded}&plotno={plot_no}"
        return url
    except Exception as e:
        print(f"❌ Error generating URL for row {row.to_dict()}: {e}")
        return None

# ---------------------------
# 4️⃣ Clean query address
# ---------------------------
def clean_address(address):
    cleaned = re.sub(r'\b(ग्रा\.|ग्राम|पं\.|प\.|जि\.)\b', '', str(address))
    return " ".join(cleaned.split())

# ---------------------------
# 5️⃣ Jaccard similarity with fuzzy matching
# ---------------------------
def jaccard_similarity(str1, str2, fuzzy_threshold=98):
    words1 = str(str1).split()
    words2 = str(str2).split()
    
    if not words1 or not words2:
        return 0.0

    matched = 0
    used_indices = set()
    
    for w1 in words1:
        for i, w2 in enumerate(words2):
            if i in used_indices:
                continue
            if fuzz.ratio(w1, w2) >= fuzzy_threshold:
                matched += 1
                used_indices.add(i)
                break

    union_size = len(words1) + len(words2) - matched
    return matched / union_size

# ---------------------------
# 6️⃣ Find closest row
# ---------------------------
def find_closest_row(query_address):
    query_cleaned = clean_address(query_address)
    best_score = -1
    best_row = None
    for idx, row in df.iterrows():
        try:
            score = jaccard_similarity(query_cleaned, row['combined_str'])
            if score > best_score:
                best_score = score
                best_row = row
        except Exception as e:
            print(f"❌ Error comparing row {idx}: {e}")
    return best_row, best_score

# ---------------------------
# 7️⃣ Extract integers from Khasra_No
# ---------------------------
def extract_integers(khasra_str):
    return [int(x) for x in re.findall(r'\d+', str(khasra_str))]

# ---------------------------
# 8️⃣ Process FRA records with retries and incremental saving
# ---------------------------
def enrich_fra_records_incremental(fra_json_path, output_path):
    with open(fra_json_path, "r", encoding="utf-8") as f:
        fra_records = json.load(f)

    enriched_records = []

    for idx, record in enumerate(fra_records, 1):
        address = record.get("Address") or record.get("Village_Details")
        khasra_str = record.get("Khasra_No")
        print(f"\nProcessing record {idx}: Address={address}, Khasra={khasra_str}")

        if not address or not khasra_str:
            record["Coordinates"] = None
            enriched_records.append(record)
            continue

        closest_row, sim = find_closest_row(address)
        if closest_row is None:
            record["Coordinates"] = None
            enriched_records.append(record)
            continue

        khasra_numbers = extract_integers(khasra_str)
        record_coords = []

        for num in khasra_numbers:
            retries = 3
            while retries > 0:
                url = generate_bhunaksha_url(closest_row, num)
                if url is None:
                    record_coords.append(None)
                    break
                try:
                    resp = requests.get(url, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        record_coords.append({
                            "plot_no": num,
                            "center_x": data.get("center_x"),
                            "center_y": data.get("center_y"),
                            "xmin": data.get("xmin"),
                            "ymin": data.get("ymin"),
                            "xmax": data.get("xmax"),
                            "ymax": data.get("ymax"),
                        })
                        break
                    else:
                        print(f"⚠️ HTTP {resp.status_code}, retrying in 10s...")
                        sleep(10)
                        retries -= 1
                except Exception as e:
                    print(f"❌ Error fetching URL {url}: {e}, retrying in 10s...")
                    sleep(10)
                    retries -= 1
            if retries == 0:
                record_coords.append(None)

        record["Coordinates"] = record_coords
        enriched_records.append(record)

        # Save incrementally
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(enriched_records, f, ensure_ascii=False, indent=2)
        sleep(0.1)

    return enriched_records

# ---------------------------
# 9️⃣ Run Example
# ---------------------------
output = enrich_fra_records_incremental("fra_records.json", "fra_records_with_coords.json")
print(json.dumps(output[:2], ensure_ascii=False, indent=2))
