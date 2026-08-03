"""Run each real teammate's own EmbeddingStore/chunker code against the
shared K4 corpus + shared 5 benchmark queries, using the real OpenAI embedder.

Every package here is the teammate's actual committed code (extracted from
their branch), not a fabrication. Run: python scripts/phase2_team_benchmark.py
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=True)

from ingest import chunk_document, load_documents

DATA_DIR = "data/k4_ecommerce"

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

# (member label, package, chunker attr name, chunker kwargs)
MEMBERS = [
    ("Vu Dinh Huy", "src.VuDinhHuy", "RecursiveChunker", {"chunk_size": 500}),
    ("Le Tuan Minh", "src.2A202601390-LeTuanMinh", "SentenceChunker", {"max_sentences_per_chunk": 3}),
    ("Nguyen Thi Nam Phuong", "src.NguyenThiNamPhuong", "RecursiveChunker", {"chunk_size": 500}),
    ("Le Quang Trung", "src._trunglq_root_impl", "RecursiveChunker", {"chunk_size": 500}),
]


def run_member(label: str, package: str, chunker_name: str, chunker_kwargs: dict) -> None:
    mod = importlib.import_module(package)
    OpenAIEmbedder = getattr(mod, "OpenAIEmbedder")
    EmbeddingStore = getattr(mod, "EmbeddingStore")
    ChunkerClass = getattr(mod, chunker_name)

    embedder = OpenAIEmbedder()
    chunker = ChunkerClass(**chunker_kwargs)

    chunk_docs = []
    for doc in load_documents(DATA_DIR):
        chunk_docs.extend(chunk_document(doc, chunker))

    store = EmbeddingStore(collection_name=f"team_bench_{label}", embedding_fn=embedder)
    store.add_documents(chunk_docs)

    print(f"\n{'=' * 70}\n{label}  |  package={package}  |  chunker={chunker_name}{chunker_kwargs}  |  chunks={store.get_collection_size()}\n{'=' * 70}")

    for item in QUERIES:
        question = item["question"]
        metadata_filter = item["metadata_filter"]
        if metadata_filter:
            results = store.search_with_filter(question, top_k=3, metadata_filter=metadata_filter)
        else:
            results = store.search(question, top_k=3)

        print(f"\nCâu hỏi: {question}")
        for rank, result in enumerate(results, start=1):
            preview = result["content"][:150].replace("\n", " ")
            doc_id = result["metadata"].get("doc_id")
            print(f"  {rank}. score={result['score']:.4f} doc_id={doc_id}")
            print(f"     {preview}...")


def main() -> int:
    for label, package, chunker_name, chunker_kwargs in MEMBERS:
        try:
            run_member(label, package, chunker_name, chunker_kwargs)
        except Exception as error:
            print(f"\n!!! {label} ({package}) FAILED: {type(error).__name__}: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
