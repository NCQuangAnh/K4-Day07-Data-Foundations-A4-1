"""Reproduce the five sentence-pair similarities reported in REPORT_CANHAN.md."""

from __future__ import annotations

from sentence_transformers import SentenceTransformer

from src.VuDinhHuy import LOCAL_EMBEDDING_MODEL, compute_similarity


PAIRS = [
    (
        "Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày sau khi nhận hàng.",
        "Người mua được phép trả lại sản phẩm và nhận tiền hoàn lại trong 7 ngày kể từ ngày giao hàng.",
    ),
    (
        "Đơn hàng sẽ được giao trong vòng ba ngày làm việc.",
        "Thời gian vận chuyển dự kiến của đơn hàng là ba ngày làm việc.",
    ),
    (
        "Chính sách đổi trả cho phép khách hàng hoàn lại sản phẩm bị lỗi.",
        "Python là một ngôn ngữ lập trình phổ biến trong khoa học dữ liệu.",
    ),
    (
        "Người bán phải cung cấp hóa đơn cho người mua.",
        "Người bán không cần cung cấp hóa đơn cho người mua.",
    ),
    (
        "Người mua có thể hủy đơn hàng trước khi sản phẩm được giao.",
        "The buyer can cancel the order before the product is delivered.",
    ),
]


def main() -> None:
    model = SentenceTransformer(LOCAL_EMBEDDING_MODEL, local_files_only=True)
    sentences = [sentence for pair in PAIRS for sentence in pair]
    vectors = model.encode(sentences, normalize_embeddings=True)

    for index in range(len(PAIRS)):
        score = compute_similarity(
            vectors[index * 2].tolist(),
            vectors[index * 2 + 1].tolist(),
        )
        print(f"Pair {index + 1}: {score:.6f}")


if __name__ == "__main__":
    main()
