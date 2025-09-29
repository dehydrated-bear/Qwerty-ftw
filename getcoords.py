import pandas as pd
import re
import json
import requests
from time import sleep
from fuzzywuzzy import fuzz
# 1️⃣ Load CSV
csv_path = "baran_location_hierarchy.csv"
print(f"📂 Loading CSV: {csv_path}")
df = pd.read_csv(csv_path)

# Strip column names
df.columns = df.columns.str.strip()
print(f"✅ Columns after strip: {df.columns.tolist()}")

# Columns for combined string
name_cols = ["District_Name", "Tehsil_Name", "RI_Name", "Halka_Name", "Village_Name"]
id_cols = ["District_ID", "Tehsil_ID", "RI_ID", "Halka_ID", "Village_ID"]

# 2️⃣ Preprocess rows
def preprocess_row(row):
    combined = " ".join(str(row[col]).strip() for col in name_cols)
    if combined.strip().lower().endswith("digitized"):
        return None
    return combined

df['combined_str'] = df.apply(preprocess_row, axis=1)
df = df[df['combined_str'].notna()]
print(f"✅ Rows after preprocessing: {len(df)}")

# 3️⃣ Bhunaksha URL generator
def generate_bhunaksha_url(row, plot_no):
    try:
        numbers = [
            str(row["District_ID"]),        # keep as-is
            str(row["Tehsil_ID"]).zfill(3), # keep as-is
            str(row["RI_ID"]),               # keep as-is
            str(int(row["Halka_ID"])).zfill(5),
            str(row["Village_ID"])           # keep as-is
        ]
        unique_numbers = numbers + ["001"]
        levels_str = ",".join(unique_numbers) + ","
        levels_encoded = levels_str.replace(",", "%2C")
        url = f"https://bhunaksha.rajasthan.gov.in/Viewmap/ScalarDatahandler?OP=5&state=08&levels={levels_encoded}&plotno={plot_no}"
        print(f"🔗 Generated URL: {url}")
        return url
    except Exception as e:
        print(f"❌ Error generating URL for row {row.to_dict()}: {e}")
        return None

# 4️⃣ Clean query address
def clean_address(address):
    try:
        cleaned = re.sub(r'\b(ग्रा\.|ग्राम|पं\.|प\.|जि\.)\b', '', str(address))
        cleaned = " ".join(cleaned.split())
        return cleaned
    except Exception as e:
        print(f"❌ Error cleaning address '{address}': {e}")
        return str(address)

# 5️⃣ Jaccard similarity
def jaccard_similarity(str1, str2, fuzzy_threshold=98):
    """
    Jaccard similarity at word level using fuzzy matching:
    - Each word in str1 is compared to all words in str2
    - If fuzzy similarity >= threshold, count as a match
    """
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

    # Union size = total unique words across both strings
    union_size = len(words1) + len(words2) - matched
    return matched / union_size

# 6️⃣ Find closest row
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
    print(f"best row:", best_row, "\n")
    print(f"🧮 Best similarity for '{query_address}' is {best_score:.2f} besr")
    return best_row, best_score

# 7️⃣ Process FRA records with incremental saving and debug
def enrich_fra_records_incremental(fra_json_path, output_path, max_retries=3, retry_wait=10):
    print(f"📂 Loading FRA records: {fra_json_path}")
    with open(fra_json_path, "r", encoding="utf-8") as f:
        fra_records = json.load(f)
    print(f"✅ Total records loaded: {len(fra_records)}")

    enriched_records = []

    for idx, record in enumerate(fra_records, 1):
        print(f"\n🔹 Processing record {idx}/{len(fra_records)}")
        address = record.get("Address") or record.get("Village_Details")
        khasra = record.get("Khasra_No")
        print(f"   Address: {address}, Khasra: {khasra}")

        if not address or not khasra:
            print(f"⚠️ Skipping record (missing Address or Khasra_No)")
            record["Coordinates"] = None
            enriched_records.append(record)
            continue

        closest_row, sim = find_closest_row(address)
        if closest_row is None:
            print(f"❌ No matching row found for address: {address}")
            record["Coordinates"] = None
            enriched_records.append(record)
            continue

        url = generate_bhunaksha_url(closest_row, khasra)
        if url is None:
            record["Coordinates"] = None
            enriched_records.append(record)
            continue

        # 🔹 HTTP request with retry logic
        retries = 0
        while retries <= max_retries:
            try:
                resp = requests.get(url, timeout=30)
                print(f"   HTTP Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}")
                
                if resp.status_code == 200:
                    data = resp.json()
                    record["Coordinates"] = {
                        "center_x": data.get("center_x"),
                        "center_y": data.get("center_y"),
                        "xmin": data.get("xmin"),
                        "ymin": data.get("ymin"),
                        "xmax": data.get("xmax"),
                        "ymax": data.get("ymax"),
                    }
                    print(f"   ✅ Coordinates fetched for Khasra {khasra}")
                    break  # success, exit retry loop

                elif resp.status_code == 530:
                    retries += 1
                    print(f"   ⚠️ Server error 530. Retry {retries}/{max_retries} after {retry_wait}s...")
                    sleep(retry_wait)
                    continue
                else:
                    print(f"   ❌ Failed to fetch JSON or invalid content type. Preview: {resp.text[:200]}")
                    record["Coordinates"] = None
                    break

            except Exception as e:
                retries += 1
                print(f"   ❌ Error fetching Bhunaksha API: {e}. Retry {retries}/{max_retries} after {retry_wait}s...")
                sleep(retry_wait)
                if retries > max_retries:
                    record["Coordinates"] = None
                    break

        enriched_records.append(record)

        # 🔹 Save incrementally
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(enriched_records, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(enriched_records)} records to {output_path}")
        except Exception as e:
            print(f"Error saving JSON: {e}")
        sleep(0.1)

    print(f"\n📁 All records processed. Final save to {output_path}")
    return enriched_records

# 🔹 Example usage
output = enrich_fra_records_incremental("fra_records.json", "fra_records_with_coords.json")
print(json.dumps(output[:2], ensure_ascii=False, indent=2))