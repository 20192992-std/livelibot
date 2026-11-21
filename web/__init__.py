from flask import Flask

from llm.assistant import Assistant
from rag.vector_store import VectorStore
from rag.embedding import EmbeddingModel
from web.routes.chat import chat_bp

print("Loading embedding model...")
embedding_model = EmbeddingModel()
print("Embedding model loaded!")

print("Connecting to vector store...")
store = VectorStore(
    db_path="chroma_db",
    name="knowledge",
    embedding_model=embedding_model,
    batch_size=32,
)
print("Vector store connected!")

assistant = Assistant(store)

def create_app():
    app = Flask(__name__)

    app.extensions["assistant"] = assistant

    app.register_blueprint(chat_bp)

    return app