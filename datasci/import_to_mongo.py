import os
import pandas as pd
from pymongo import MongoClient

def get_db():
    mongo_uri = 'mongodb://localhost:27017/'
    db_name = 'datasci'
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
    return client[db_name]

def extract_repo_name(path):
    parts = path.split(os.sep)
    if 'repos' in parts:
        idx = parts.index('repos')
        return parts[idx + 1]
    return 'unknown'

def import_csv_to_mongo(db, csv_path, collection_name):
    try:
        df = pd.read_csv(csv_path)
        df['repo_name'] = extract_repo_name(csv_path)
        records = df.to_dict(orient='records')
        if records:
            db[collection_name].insert_many(records)
            print(f"[OK] Imported {csv_path} -> MongoDB collection '{collection_name}'")
        else:
            print(f"[EMPTY] {csv_path} is empty")
    except Exception as e:
        print(f"[ERROR] Failed to import {csv_path}: {e}")

def main():
    base_dir = os.path.join(os.getcwd(), 'notebooks', 'data', 'repos')
    print(f"[INFO] Searching in: {base_dir}")

    db = get_db()

    if not os.path.exists(base_dir):
        print("[ERROR] Base directory does not exist!")
        return

    found_any_csv = False

    for root, dirs, files in os.walk(base_dir):
        print(f"[DEBUG] Entering directory: {root}")
        for file in files:
            print(f"[DEBUG] Found file: {file}")
            if file.endswith('.csv'):
                found_any_csv = True
                csv_path = os.path.join(root, file)
                collection_name = file.replace(".csv", "")
                import_csv_to_mongo(db, csv_path, collection_name)

    if not found_any_csv:
        print("[WARNING] No CSV files found!")

if __name__ == "__main__":
    main()
