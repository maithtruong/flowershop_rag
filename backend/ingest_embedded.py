import pymongo
from dotenv import load_dotenv
import os
import pandas as pd
from sentence_transformers import SentenceTransformer


# Load environment variables
load_dotenv()
DB_URL = os.getenv("DB_URL")

# Initialize embedding model
embedding_model = SentenceTransformer("keepitreal/vietnamese-sbert")


def get_embedding(text):
    """Generate embedding for a given text string."""
    if not text.strip():
        print("Attempted to get embedding for empty text.")
        return []

    embedding = embedding_model.encode(text)
    return embedding.tolist()


def main():
    # Connect to MongoDB
    client = pymongo.MongoClient(DB_URL)
    db = client['flowershop']
    raw_collection = db['raw_product_details']
    embedded_collection = db['embedded_product_details']

    # Load raw documents from MongoDB
    data = list(raw_collection.find())
    raw_df = pd.DataFrame(data)

    # Combine relevant fields into a single text field for embedding
    raw_df['all_text'] = (
        "URL: " + raw_df['url'] +
        " Description: " + raw_df['content'] +
        " Price: " + raw_df['price'] +
        " Title: " + raw_df['title']
    )

    # Generate embeddings for combined text
    raw_df['embedded_all_text'] = raw_df['all_text'].apply(get_embedding)

    # Store embedded documents in MongoDB
    embedded_documents = raw_df.to_dict('records')
    embedded_collection.insert_many(embedded_documents)


if __name__ == "__main__":
    main()