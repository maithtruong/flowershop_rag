import pymongo
from dotenv import load_dotenv
import os
import pandas as pd


## Environment
load_dotenv()
DB_URL = os.getenv("DB_URL")

def main():
    ## Data
    df = pd.read_json("data/output.json")

    # MongoDB
    client = pymongo.MongoClient(DB_URL)
    db = client['flowershop']
    raw_collection = db['raw_product_details']

    ### Ingest Data
    raw_documents = df.to_dict("records")
    raw_collection.insert_many(raw_documents)


if __name__ == "__main__":
    main()