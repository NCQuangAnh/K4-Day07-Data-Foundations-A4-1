"""Phase 2 benchmark runner (personal, NguyenCaoQuangAnh).

Compares baseline FixedSizeChunker vs custom HeadingChunker on the K4
e-commerce corpus using 5 agreed benchmark queries. Uses the real OpenAI
embedder (not mock) so scores reflect actual semantic similarity.

Run: python scripts/phase2_benchmark.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=True)

from ingest import chunk_document, load_documents
from src.NguyenCaoQuangAnh.chunking import FixedSizeChunker
from src.NguyenCaoQuangAnh.embeddings import OpenAIEmbedder
from src.NguyenCaoQuangAnh.heading_chunker import HeadingChunker, SectionAwareChunker
from src.NguyenCaoQuangAnh.store import EmbeddingStore

DATA_DIR = "data/k4_ecommerce"


def build_knowledge_base(data_dir: str, embedding_fn, chunker) -> EmbeddingStore:
    """Same pipeline as ingest.build_knowledge_base but using the
    src.NguyenCaoQuangAnh.EmbeddingStore implementation (root src/ is the
    untouched template and still raises NotImplementedError)."""
    chunk_docs = []
    for doc in load_documents(data_dir):
        chunk_docs.extend(chunk_document(doc, chunker))
    store = EmbeddingStore(collection_name="phase2_bench", embedding_fn=embedding_fn)
    store.add_documents(chunk_docs)
    return store

QUERIES = [
    {
        "question": "Người mua có thể yêu cầu trả hàng/hoàn tiền trong trường hợp nào?",
        "metadata_filter": {"customer_role": "buyer"},
    },
    {
        "question": "Người bán cần tuân thủ quy định pháp luật nào khi đăng bán sản phẩm trên Shopee?",
        "metadata_filter": {"customer_role": "seller"},
    },
    {
        "question": "Shopee chấp nhận những phương thức thanh toán nào?",
        "metadata_filter": None,
    },
    {
        "question": "Danh sách hàng cấm giao dịch trên Shopee gồm những nhóm sản phẩm nào?",
        "metadata_filter": None,
    },
    {
        "question": "Quy trình giải quyết tranh chấp giữa người mua và người bán trên Shopee gồm mấy bước?",
        "metadata_filter": None,
    },
]


def run_strategy(name: str, chunker) -> None:
    embedder = OpenAIEmbedder()
    store = build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=chunker)
    print(f"\n{'=' * 70}\nChiến lược: {name}  |  tổng số chunk: {store.get_collection_size()}\n{'=' * 70}")

    for item in QUERIES:
        question = item["question"]
        metadata_filter = item["metadata_filter"]
        if metadata_filter:
            results = store.search_with_filter(question, top_k=3, metadata_filter=metadata_filter)
        else:
            results = store.search(question, top_k=3)

        print(f"\nCâu hỏi: {question}")
        if metadata_filter:
            print(f"  (metadata_filter={metadata_filter})")
        for rank, result in enumerate(results, start=1):
            preview = result["content"][:150].replace("\n", " ")
            doc_id = result["metadata"].get("doc_id")
            print(f"  {rank}. score={result['score']:.4f} doc_id={doc_id}")
            print(f"     {preview}...")


def main() -> int:
    run_strategy("Baseline - FixedSizeChunker(chunk_size=500, overlap=50)", FixedSizeChunker(chunk_size=500, overlap=50))
    run_strategy("Custom v1 - HeadingChunker(max_chunk_size=2000)", HeadingChunker(max_chunk_size=2000))
    run_strategy("Custom v2 - SectionAwareChunker(max_chunk_size=400)", SectionAwareChunker(max_chunk_size=400))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
