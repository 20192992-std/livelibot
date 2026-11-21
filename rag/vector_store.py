
import re
from pathlib import Path

import chromadb
from rag.embedding import EmbeddingModel

class VectorStore:
    def __init__(
        self,
        db_path: str | Path,
        name: str,
        embedding_model: EmbeddingModel,
        batch_size: int = 100,
    ):
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")

        self.client = chromadb.PersistentClient(path=str(db_path))
        self.name = name
        self.embedding_model = embedding_model
        self.batch_size = batch_size

    def rebuild(self, chunks: list[dict]) -> int:
        try:
            self.client.delete_collection(self.name)
        except chromadb.errors.NotFoundError:
            pass

        collection = self.client.create_collection(self.name)

        for start in range(0, len(chunks), self.batch_size):
            batch = chunks[start:start + self.batch_size]

            texts = [
                f'{chunk["title"]}\n{chunk["text"]}'
                for chunk in batch
            ]

            vectors = self.embedding_model.embed_documents(texts)

            collection.add(
                ids=[chunk["id"] for chunk in batch],
                documents=[chunk["text"] for chunk in batch],
                embeddings=vectors,
                metadatas=[
                    {
                        "section": chunk.get("section", ""),
                        "title": chunk.get("title", ""),
                        "status": self.get_status(chunk["text"]),
                        "source": chunk.get("source", ""),
                        "source_type": chunk.get("source_type", ""),
                    }
                    for chunk in batch
                ],
            )

            print(f"Saved {start + len(batch)} / {len(chunks)}")

        return collection.count()

    def search(
        self,
        question: str,
        n_results: int = 5,
        where: dict | None = None,
    ) -> dict:
        collection = self.client.get_collection(self.name)

        vector = self.embedding_model.embed_query(question)

        return collection.query(
            query_embeddings=[vector],
            n_results=n_results,
            where=where,
        )

    @staticmethod
    def get_status(text: str) -> str:
        found = re.findall(r"\(Status: ([^)]*)\)", text)
        return found[-1] if found else ""
