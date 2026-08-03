# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** K4-A4-1
**Thành viên:** Lê Tuấn Minh
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm tập trung vào chính sách đổi trả, giao hàng và quyền riêng tư trong môi trường thương mại điện tử.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách đổi trả | https://example.com/returns-policy | 03/08/2026 | 4200 | category=returns, customer_role=buyer, language=vi |
| 2 | Chính sách giao hàng | https://example.com/shipping-policy | 03/08/2026 | 3800 | category=shipping, customer_role=buyer, language=vi |
| 3 | Quyền riêng tư dữ liệu | https://example.com/privacy-policy | 03/08/2026 | 5000 | category=privacy, customer_role=buyer, language=vi |
| 4 | Điều kiện người bán | https://example.com/seller-terms | 03/08/2026 | 4500 | category=seller_terms, customer_role=seller, language=vi |
| 5 | Chính sách thanh toán | https://example.com/payment-policy | 03/08/2026 | 3900 | category=payment, customer_role=buyer, language=vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| category | string | returns | Giúp lọc theo chủ đề cụ thể như đổi trả, giao hàng hoặc bảo mật. |
| customer_role | string | buyer | Cho phép phân biệt truy vấn từ người mua và người bán. |
| language | string | vi | Giảm nhiễu khi câu hỏi và tài liệu không cùng ngôn ngữ. |
| document_version | string | v1.2 | Hỗ trợ kiểm tra độ mới và truy vết nguồn tài liệu. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Chính sách đổi trả | FixedSizeChunker (`fixed_size`) | 4 | 650 | Có |
| Chính sách đổi trả | SentenceChunker (`by_sentences`) | 3 | 900 | Có |
| Chính sách đổi trả | RecursiveChunker (`recursive`) | 3 | 800 | Có |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Lê Tuấn Minh**
- **Loại chiến lược:** SentenceChunker
- **Mô tả & lý do chọn cho chủ đề này:** Chunk theo câu giúp giữ ngữ cảnh logic tốt hơn với các quy định dài và nhiều điều kiện. Với chủ đề chính sách, mỗi câu thường mang ý nghĩa rõ ràng nên cách này dễ truy xuất hơn.
- **Code snippet (nếu custom):**
```python
class SentenceChunker:
    def chunk(self, text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [" ".join(sentences[i:i+3]) for i in range(0, len(sentences), 3)]
```

**Thành viên 2 — Nhóm khác**
- **Loại chiến lược:** RecursiveChunker
- **Mô tả & lý do chọn:** Cách này phù hợp khi nội dung có cấu trúc theo đoạn văn và tiêu đề, nên tốt cho tài liệu có nhiều phần.
- **Code snippet (nếu custom):**

**Thành viên 3 — Nhóm khác**
- **Loại chiến lược:** FixedSizeChunker
- **Mô tả & lý do chọn:** Cách này đơn giản và dễ áp dụng, phù hợp làm baseline khi bắt đầu thử chiến lược.
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Lê Tuấn Minh | SentenceChunker | 8.5 | Giữ ngữ cảnh tốt, các câu có ý nghĩa rõ | Có thể quá dài nếu một câu chứa nhiều điều kiện |
| Nhóm khác | RecursiveChunker | 8.0 | Phù hợp với tài liệu có cấu trúc | Có thể chia nhỏ không đều |
| Nhóm khác | FixedSizeChunker | 7.0 | Đơn giản, dễ triển khai | Có thể cắt giữa ý và làm mất ngữ cảnh |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với chủ đề chính sách, chiến lược SentenceChunker thường tốt nhất vì mỗi câu thường chứa một ý nghĩa riêng và dễ truy xuất. RecursiveChunker cũng hiệu quả khi tài liệu có cấu trúc rõ, nhưng cần cài đặt kỹ hơn để tránh chia quá nhỏ.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Chính sách đổi trả có thời hạn bao lâu? | Thông thường là trong vòng 7 ngày kể từ khi nhận hàng nếu sản phẩm bị lỗi. | Chunk về đổi trả |
| 2 | Khách hàng cần làm gì nếu đơn hàng giao chậm? | Liên hệ bộ phận hỗ trợ và cung cấp thông tin đơn hàng để được xử lý. | Chunk về giao hàng |
| 3 | Chính sách bảo mật dữ liệu khách hàng như thế nào? | Dữ liệu khách hàng được bảo vệ và chỉ sử dụng cho mục đích vận hành dịch vụ. | Chunk về quyền riêng tư |
| 4 | Người bán cần đáp ứng những điều kiện gì? | Cần cung cấp thông tin chính xác và tuân thủ quy định của nền tảng. | Chunk về điều kiện người bán |
| 5 | Phương thức thanh toán nào được hỗ trợ? | Nền tảng hỗ trợ thanh toán bằng thẻ, ví điện tử hoặc chuyển khoản. | Chunk về thanh toán |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Chính sách đổi trả có thời hạn bao lâu? | SentenceChunker | Có | Chunk về đổi trả xuất hiện ở top-1 |
| 2 | Khách hàng cần làm gì nếu đơn hàng giao chậm? | RecursiveChunker | Có | Câu hỏi cụ thể dễ match với chunk về xử lý đơn hàng |
| 3 | Chính sách bảo mật dữ liệu khách hàng như thế nào? | SentenceChunker | Có | Metadata category=privacy giúp tăng độ chính xác |
| 4 | Người bán cần đáp ứng những điều kiện gì? | SentenceChunker | Có | Câu hỏi cần lọc theo customer_role=seller |
| 5 | Phương thức thanh toán nào được hỗ trợ? | FixedSizeChunker | Có | Chunk ngắn dễ trả về kết quả đúng |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Metadata giúp ích rất nhiều ở các câu hỏi liên quan đến vai trò người dùng hoặc chủ đề cụ thể, ví dụ câu hỏi về điều kiện người bán và chính sách bảo mật. Nếu không lọc metadata, kết quả có thể bị nhiễu do nhiều tài liệu cùng chủ đề.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - Chunking phù hợp giúp retrieval tốt hơn rất nhiều so với việc để một tài liệu quá dài. 
> - Metadata là yếu tố quan trọng để lọc câu hỏi theo vai trò và chủ đề. 
> - Cấu trúc câu và ngữ cảnh của chính sách cần được giữ nguyên để agent trả lời đúng.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu nhưng chiến lược chunking khác nhau có thể dẫn đến kết quả retrieval khác biệt. SentenceChunker phù hợp hơn cho chính sách vì giữ được ý nghĩa của từng câu, còn FixedSizeChunker dễ cắt mất ngữ cảnh.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ thu thập nhiều tài liệu có cấu trúc rõ hơn và gắn metadata chi tiết hơn như `category`, `customer_role`, `document_version`. Điều này giúp hệ thống retrieval có khả năng trả về kết quả chính xác và dễ kiểm tra hơn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 9 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **36 / 40** |
