from __future__ import annotations

import re

from .chunking import RecursiveChunker


class HeadingChunker:
    """Chiến lược chia nhỏ tùy chỉnh cho chủ đề chính sách TMĐT (K4).

    Lý do thiết kế: các văn bản quy chế/chính sách thu thập được (Shopee) có cấu trúc
    heading La Mã cấp cao rõ ràng (I., II., III., ...), mỗi mục là một điều khoản trọn
    vẹn về ý nghĩa (nguyên tắc chung, quy trình thanh toán, bảo vệ thông tin cá nhân...).
    Chia theo heading giữ nguyên ngữ cảnh trọn vẹn của từng điều khoản thay vì cắt ngang
    ý như FixedSizeChunker, và tránh vỡ vụn quá mức như SentenceChunker. Mục quá dài (vd.
    danh sách hàng cấm) được chia nhỏ tiếp bằng RecursiveChunker để vẫn nằm trong giới hạn
    kích thước, thay vì tạo ra một chunk khổng lồ duy nhất.
    """

    HEADING_PATTERN = re.compile(r"^[IVXLCDM]+\.\s+\S")

    def __init__(self, max_chunk_size: int | None = 2000) -> None:
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        sections: list[list[str]] = []
        current: list[str] = []
        for line in text.splitlines():
            if self.HEADING_PATTERN.match(line.strip()):
                if current:
                    sections.append(current)
                current = [line]
            else:
                current.append(line)
        if current:
            sections.append(current)

        if not sections:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        for section_lines in sections:
            content = "\n".join(section_lines).strip()
            if not content:
                continue
            if self.max_chunk_size and len(content) > self.max_chunk_size:
                chunks.extend(RecursiveChunker(chunk_size=self.max_chunk_size).chunk(content))
            else:
                chunks.append(content)
        return chunks


class SectionAwareChunker:
    """Biến thể của HeadingChunker: tách thêm theo heading phụ (số Ả Rập,
    vd. "6. Quy trình giải quyết tranh chấp") bên trong mỗi mục La Mã, và
    luôn giữ dòng tiêu đề (La Mã + số) dính vào đầu mỗi chunk con.

    Lý do thiết kế: nhiều mục La Mã (vd. Mục III) chứa nhiều quy trình con
    dùng chung khuôn mẫu "Bước 1, Bước 2..." (mua hàng, thanh toán, giải
    quyết tranh chấp). Nếu chỉ tách theo heading La Mã rồi cắt tiếp bằng
    RecursiveChunker, tiêu đề heading phụ có thể bị tách khỏi phần "Bước 1..."
    của chính nó, khiến chunk mất ngữ cảnh chủ đề và dễ bị nhầm với quy trình
    khác có cùng khuôn mẫu câu. Giữ tiêu đề dính vào chunk giúp vector embedding
    "nhớ" đúng chủ đề của từng quy trình.
    """

    TOP_HEADING = re.compile(r"^[IVXLCDM]+\.\s+\S")
    SUB_HEADING = re.compile(r"^\d+\.\s+\S")

    def __init__(self, max_chunk_size: int | None = 1200) -> None:
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        top_sections = self._split_by(text.splitlines(), self.TOP_HEADING)
        chunks: list[str] = []
        for top_heading, top_lines in top_sections:
            sub_sections = self._split_by(top_lines, self.SUB_HEADING)
            for sub_heading, sub_lines in sub_sections:
                body = "\n".join(sub_lines).strip()
                if not body:
                    continue
                prefix_parts = [part for part in (top_heading, sub_heading) if part]
                prefix = " | ".join(prefix_parts)
                content = f"{prefix}\n{body}" if prefix and prefix not in body else body
                if self.max_chunk_size and len(content) > self.max_chunk_size:
                    for piece in RecursiveChunker(chunk_size=self.max_chunk_size).chunk(body):
                        chunks.append(f"{prefix}\n{piece}" if prefix else piece)
                else:
                    chunks.append(content)
        return chunks

    @staticmethod
    def _split_by(lines: list[str], pattern: re.Pattern) -> list[tuple[str, list[str]]]:
        sections: list[tuple[str, list[str]]] = []
        heading = ""
        current: list[str] = []
        for line in lines:
            if pattern.match(line.strip()):
                if current:
                    sections.append((heading, current))
                heading = line.strip()
                current = [line]
            else:
                current.append(line)
        if current:
            sections.append((heading, current))
        return sections
