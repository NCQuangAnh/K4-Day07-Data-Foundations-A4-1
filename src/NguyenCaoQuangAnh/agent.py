from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        context = "\n\n".join(f"- {result['content']}" for result in results)
        prompt = (
            "Trả lời câu hỏi CHỈ dựa trên ngữ cảnh (context) dưới đây. "
            "Nếu context không đủ thông tin, hãy nói rõ là không biết.\n\n"
            f"Context:\n{context}\n\n"
            f"Câu hỏi: {question}\n"
            "Trả lời:"
        )
        return self.llm_fn(prompt)
