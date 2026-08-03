# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thị Nam Phương  
**Nhóm:** A4-2
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn bản có độ tương tự cosine cao khi các vector biểu diễn của chúng
> hướng gần giống nhau. Điều này thường cho thấy hai đoạn có chủ đề hoặc ý nghĩa
> ngữ nghĩa gần nhau, dù chúng không nhất thiết dùng đúng cùng một từ.

**Ví dụ có độ tương tự CAO:**
- Câu A: Khách hàng có thể trả lại sản phẩm trong vòng 30 ngày.
- Câu B: Người mua được phép hoàn trả hàng trước khi hết thời hạn 30 ngày.
- Tại sao tương đồng: Hai câu cùng mô tả quyền đổi trả và cùng nêu thời hạn 30 ngày.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Đơn hàng sẽ được giao trong ba ngày làm việc.
- Câu B: Mạng nơ-ron học đặc trưng từ dữ liệu huấn luyện.
- Tại sao khác: Một câu nói về vận chuyển trong thương mại điện tử, câu còn lại nói về học máy.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào hướng của vector, tức mẫu phân bố đặc trưng mang ý nghĩa,
> và ít bị ảnh hưởng bởi độ lớn của vector. Khoảng cách Euclid nhạy với độ lớn nên
> hai vector cùng hướng nhưng khác độ dài vẫn có thể bị xem là cách xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: `ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.111...)`.  
> Đáp án: **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap bằng 100, số chunk là
> `ceil((10,000 - 100) / (500 - 100)) = ceil(9,900 / 400) = 25`, tăng từ 23 lên
> 25 chunks. Chồng chéo nhiều hơn giúp giữ lại ngữ cảnh nằm sát ranh giới hai
> chunk, giảm nguy cơ một ý quan trọng bị cắt rời, nhưng làm tăng dữ liệu lưu trữ
> và chi phí nhúng/truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\r?\n+)` để tách tại khoảng trắng hoặc
> xuống dòng đứng sau dấu `.`, `!`, `?`, đồng thời giữ lại dấu câu ở cuối câu.
> Sau khi tách, mỗi câu được chuẩn hóa khoảng trắng và ghép theo
> `max_sentences_per_chunk`; văn bản rỗng chỉ trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán lần lượt thử các separator theo độ ưu tiên, giữ separator ở cuối
> phần trước rồi gộp các phần nhỏ đến gần `chunk_size`. Phần còn quá dài được xử
> lý đệ quy với separator tiếp theo. Base case là đoạn đã không vượt kích thước;
> nếu hết separator thì cắt theo số ký tự để luôn kết thúc an toàn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuyển thành record độc lập gồm `id`, `content`, bản sao
> `metadata` và embedding, rồi lưu trong danh sách in-memory. Khi tìm kiếm, truy
> vấn chỉ được nhúng một lần; tích vô hướng giữa vector truy vấn và từng embedding
> được dùng làm score, sau đó sắp xếp giảm dần và lấy tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc trước các record thỏa tất cả cặp key-value trong
> metadata rồi mới tính điểm, nhờ đó các ứng viên ngoài phạm vi không ảnh hưởng
> xếp hạng. `delete_document` tạo lại danh sách và loại toàn bộ record có
> `metadata['doc_id']` trùng với mã cần xóa, đồng thời trả về liệu có record nào
> thực sự bị xóa hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` lấy top-k chunk liên quan từ store, đánh số từng chunk và ghép chúng
> vào phần `NGỮ CẢNH` của prompt trước câu hỏi. Prompt yêu cầu LLM chỉ dựa vào ngữ
> cảnh và thừa nhận thiếu thông tin khi cần; sau đó toàn bộ prompt được chuyển cho
> `llm_fn` để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$env:LAB_SOLUTION_PACKAGE='src.NguyenThiNamPhuong'
$env:PYTHONDONTWRITEBYTECODE='1'
py -3.11 -m pytest tests -v -p no:cacheprovider

============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1
collected 42 items

tests/test_solution.py ..........................................       [100%]

============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Chưa thực hiện trong Giai đoạn 1; mục này thuộc hoạt động so sánh của Giai đoạn 2.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

> Chưa thực hiện trong Giai đoạn 1; mục này cần bộ 5 câu hỏi chung của nhóm ở Giai đoạn 2.

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | Chưa thực hiện (Giai đoạn 2) |
| Kết quả truy xuất của tôi (Competition Results) | Chưa thực hiện (Giai đoạn 2) |
| **Tổng các mục đã thực hiện trong Giai đoạn 1** | **45 / 45** |
