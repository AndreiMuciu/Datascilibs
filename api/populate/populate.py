import pandas as pd
from pymongo import MongoClient

# Configuration
csv_file = 'data.csv'
mongo_uri = 'mongodb://localhost:27017/'
db_name = 'datasci'
collection_name = 'repos'

if __name__ == '__main__':
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    df = pd.read_csv(csv_file)

    # Replace all NaN with None
    df = df.where(pd.notnull(df), None)

    for _, row in df.iterrows():
        doc = row.to_dict()
        doc['_id'] = doc.pop('rank')
        try:
            collection.insert_one(doc)
        except Exception as e:
            print(f"Error inserting rank {doc['_id']}: {e}")

    print("Insertion complete.")