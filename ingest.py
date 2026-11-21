
from anyio import Path
from rag.data_loader import DataLoader
from rag.vector_store import VectorStore
from rag.embedding import EmbeddingModel

def main():
    loader = DataLoader(
        folder=Path("documents"),
        chunk_size=800,
        overlap=100,
    )

    print(f"loading data.")

    chunks = loader.load()

    print(f"Loaded {len(chunks)} chunks.")

    embedding_model = EmbeddingModel()

    vector_store = VectorStore(
        db_path = "chroma_db",
        name = "knowledge",
        embedding_model=embedding_model,
        batch_size=32,
    )

    print("Rebuilding vector database...")

    total = vector_store.rebuild(chunks)

    print(f"Successfully indexed {total} chunks.")

if __name__ == "__main__":
    main()