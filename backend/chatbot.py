from dotenv import load_dotenv
import os
import pymongo

# LLM + Embeddings
from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables.history import RunnableWithMessageHistory

# Web server
from pyngrok import ngrok
from flask import Flask, jsonify, request
from flask_cors import CORS


# Load environment variables
load_dotenv()
DB_URL = os.getenv("DB_URL")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# Initialize embedding model
embedding_model = SentenceTransformer("keepitreal/vietnamese-sbert")

# Initialize LLM model (via OpenRouter)
model_name = "tngtech/deepseek-r1t2-chimera:free"
model = ChatOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    model=model_name,
)


# MongoDB setup
client = pymongo.MongoClient(DB_URL)
db = client['flowershop']
embedded_collection = db['embedded_product_details']


def get_embedding(text):
    """Generate embedding for input text."""
    if not text.strip():
        print("Attempted to get embedding for empty text.")
        return []

    embedding = embedding_model.encode(text)
    return embedding.tolist()


def vector_search(user_query, collection, limit=4):
    """
    Perform vector search in MongoDB using Atlas Vector Search.
    """
    query_embedding = get_embedding(user_query)

    if query_embedding is None:
        return []

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "queryVector": query_embedding,
                "path": "embedded_all_text",
                "numCandidates": 320,
                "limit": limit,
            }
        },
        {"$unset": "embedded_all_text"},
        {
            "$project": {
                "_id": 0,
                "url": 1,
                "content": 1,
                "price": 1,
                "title": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    return list(collection.aggregate(pipeline))


def get_search_result(query, collection):
    """Retrieve formatted product context from vector search."""
    results = vector_search(query, collection, 10)
    search_result = ""
    i = 0

    for result in results:
        if result.get("price"):
            i += 1
            search_result += f"\n{i}) Tên: {result.get('title')}"

            search_result += f", Giá: {result.get('price') or 'Liên hệ để trao đổi thêm!'}"

            if result.get("content"):
                search_result += f", Nội dung mô tả: {result.get('content')}"

    return search_result


def rewrite_user_message_with_context(user_message, collection):
    """
    Augment user query with retrieved product information.
    """
    search_result = get_search_result(user_message, collection)

    return f"""
    Bạn là một chuyên gia chăm sóc khách hàng tại một shop bán hoa.
    Câu hỏi của người dùng: {user_message}
    Dựa vào thông tin sản phẩm sau đây (nếu cần), hãy trả lời câu hỏi:
    {search_result}
    """


# In-memory chat history store
store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Retrieve or create chat history for a session."""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


with_message_history = RunnableWithMessageHistory(model, get_session_history)


def main():
    # Initialize Flask app
    app = Flask(__name__)
    CORS(app)

    @app.route('/chat', methods=['POST'])
    def chat():
        user_message = request.json.get('message', {}).get("content", "")
        session_id = request.json.get('sessionId', 'default')

        config = {"configurable": {"session_id": session_id}}

        # Retrieve context and rewrite prompt
        rewritten_prompt = rewrite_user_message_with_context(
            user_message, embedded_collection
        )

        # Invoke model with session history
        response = with_message_history.invoke(
            [HumanMessage(content=rewritten_prompt)],
            config=config,
        )

        return jsonify({
            "content": response.content,
            "role": "assistant",
        })

    # Start ngrok tunnel
    url = ngrok.connect(5000)
    print(f" * ngrok tunnel: {url}")

    # Start Flask server
    app.run(port=5000)


if __name__ == "__main__":
    main()