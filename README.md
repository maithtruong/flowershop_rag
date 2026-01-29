# 🌸 flowershop_rag

A simple, naive RAG chatbot that recommends products based on flower shop data.
It uses a free LLM, vector search using a Vietnamese embedding model, and simple UI using Streamlit.

## 📸 App Demo

![App demo](media/chat_output.png)

---

## ⚙️ Setup

You’ll need a few external services before running the app.

### 🔑 Required Services

* **ngrok** – exposes your local backend

  * Get your auth token from 👉 [https://ngrok.com](https://ngrok.com)

* **MongoDB Atlas** – stores product + vector data

  * Create a cluster
  * Create a DB user
  * Copy the connection string (DB URL)

* **OpenRouter** – LLM API (cheap + flexible)

  * Generate an API key 👉 [https://openrouter.ai](https://openrouter.ai)

---

### 🐍 Python Environment

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate    # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### 🔐 Environment Variables

Create a `.env` file inside the `backend/` folder:

```bash
touch backend/.env
```

Add the following:

```env
MONGO_DB_USER=your_username
MONGO_DB_PASS=your_password
DB_URL=your_mongodb_connection_string
OPENROUTER_API_KEY=your_openrouter_key
NGROK_KEY=your_ngrok_token
```

---

## 🧠 MongoDB Atlas Setup

Create a database named **`flower_shop`** with the following collections:

* `raw_product_details` — stores raw product data
* `embedded_product_details` — stores vector-embedded data

---

### 📥 Data Ingestion

Run the ingestion scripts in order:

```bash
python backend/ingest_raw.py
python backend/ingest_embedded.py
```

This will populate MongoDB with both the original product data and their embeddings.

---

### 🔎 Vector Search Configuration

In MongoDB Atlas, create a **Vector Search index** on the
`embedded_product_details` collection using the config below:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedded_all_text",
      "numDimensions": 768,
      "similarity": "cosine"
    }
  ]
}
```

---

### 🚀 Run the App

Start the backend:

```bash
python backend/chatbot.py
```

Start the frontend:

```bash
streamlit run app.py
```

---

## 🔄 Workflow

This is my general pipeline to create the app:

1. Fetch raw product data
2. Create database collections
3. Ingest product data into MongoDB
4. Generate embeddings
5. Store embedded data
6. Create MongoDB Vector Search index
7. Run the backend RAG model
8. Serve results through the Streamlit UI