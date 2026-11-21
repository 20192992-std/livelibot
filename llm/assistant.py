
import json
import urllib.error
import urllib.request

from config.llm_config import (
    CHAT_API_KEY,
    CHAT_MODEL,
    CHAT_URL,
    MAX_DISTANCE,
    MAX_TOKENS,
    N_RESULTS,
    NO_ANSWER,
    SYSTEM_PROMPT,
    TEMPERATURE,
    TOP_P,
)

class Assistant:
    def __init__(self, store):
        self.store = store

    def ask(self, question):
        results = self.store.search(question, n_results=N_RESULTS)
        chunks = self.pick_chunks(results)

        if not chunks:
            return {"answer": NO_ANSWER, "sources": []}

        context = "\n\n".join(
            f"[{chunk['id']}] {chunk['title']}\n{chunk['text']}" for chunk in chunks
        )
        answer = self.chat(context, question)

        return {
            "answer": answer,
            "sources": [
                {"id": chunk["id"], "title": chunk["title"], "source": chunk["source"]}
                for chunk in chunks
            ],
        }

    def chat(self, context, question):
        payload = {
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "max_tokens": MAX_TOKENS,
        }
        request = urllib.request.Request(
            CHAT_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                "Authorization": f"Bearer {CHAT_API_KEY}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")
            raise RuntimeError(f"Chat API error {error.code}: {detail}") from error
        except TimeoutError as error:
            raise RuntimeError("Chat API timed out after 120 s") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"Chat API unreachable: {error.reason}") from error

        return data["choices"][0]["message"]["content"].strip()

    def pick_chunks(self, results):
        """Keeps only the chunks that are close enough to the question."""
        chunks = []
        for chunk_id, text, metadata, distance in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            if distance <= MAX_DISTANCE:
                chunks.append({
                    "id": chunk_id,
                    "text": text,
                    "title": metadata["title"],
                    "source": metadata.get("source", ""),
                })
        return chunks

    def normal_message(self, message):
        payload = {
            "model": CHAT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a friendly chatbot for people in "
                        "Baguio City and Benguet. "
                        "Respond naturally and politely."
                    ),
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "max_tokens": MAX_TOKENS,
        }

        import requests

        try:
            response = requests.post(
                CHAT_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {CHAT_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=120,
            )

            response.raise_for_status()

            data = response.json()

            return data["choices"][0]["message"]["content"].strip()

        except requests.RequestException as error:
            raise RuntimeError(f"Chat API error: {error}") from error