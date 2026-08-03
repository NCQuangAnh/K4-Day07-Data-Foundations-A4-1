# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Cao Quang Anh
**Nhóm:** A4-1
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

> **Lưu ý vị trí code:** phần cài đặt (implementation) của tôi nằm trong `src/NguyenCaoQuangAnh/` (mirror đầy đủ package `src`), không sửa trực tiếp `src/` gốc (giữ nguyên làm template). Chạy test bằng:
> ```bash
> LAB_SOLUTION_PACKAGE=src.NguyenCaoQuangAnh pytest tests/ -v
> ```

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có **hướng** gần giống nhau trong không gian nhiều chiều — tức là hai đoạn văn bản mang ý nghĩa/ngữ cảnh tương đồng cao, bất kể chúng khác nhau về độ dài hay cách diễn đạt câu chữ.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sản phẩm bị cấm không được đăng bán."
- Câu B: "Hàng cấm không được phép rao bán trên sàn."
- Tại sao tương đồng: cùng diễn đạt một quy tắc (cấm bán mặt hàng bị cấm) chỉ khác từ vựng ("đăng bán" ↔ "rao bán trên sàn"), gần như là câu diễn giải lại (paraphrase) của nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách bảo mật quy định cách xử lý dữ liệu cá nhân của người dùng."
- Câu B: "Đội bóng đã giành chiến thắng trong trận đấu tối qua."
- Tại sao khác: hai câu thuộc hai chủ đề hoàn toàn không liên quan (chính sách quyền riêng tư vs. thể thao), không chia sẻ ngữ nghĩa nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ đo **góc** giữa hai vector nên không bị ảnh hưởng bởi độ lớn (magnitude) của chúng — trong khi Euclidean distance bị ảnh hưởng trực tiếp bởi magnitude, nên một câu dài (vector "to" hơn do tổng hợp nhiều token) có thể bị coi là "khác xa" một câu ngắn dù ngữ nghĩa tương tự. Với text embeddings, hướng vector mới là thứ mã hoá ý nghĩa, nên cosine phản ánh đúng bản chất tương đồng ngữ nghĩa hơn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính:
> `số lượng chunk = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
>
> **Đáp án: 23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks` — tăng từ 23 lên 25 chunks (nhiều hơn, vì mỗi bước trượt (step) ngắn lại). Muốn overlap lớn hơn để giảm rủi ro một câu/ý quan trọng bị cắt đứt ngay tại ranh giới chunk — phần nội dung gần biên được lặp lại ở cả hai chunk liền kề, giúp truy xuất (retrieval) không bỏ sót ngữ cảnh, đánh đổi bằng việc tăng số lượng chunk (tốn thêm dung lượng lưu trữ/embedding).

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `re.split(r'(?<=[.!?])\s+', text.strip())` để tách câu ngay sau dấu `.`, `!`, `?` khi theo sau là khoảng trắng (bao gồm cả xuống dòng) — `lookbehind` giữ nguyên dấu câu ở cuối mỗi câu thay vì bị regex "nuốt" mất. Sau đó strip từng câu, loại bỏ câu rỗng, rồi gộp thành từng nhóm tối đa `max_sentences_per_chunk` câu, nối bằng dấu cách. Edge case: text rỗng/toàn khoảng trắng trả về `[]`; văn bản không có dấu kết câu sẽ rơi vào đúng 1 "câu" duy nhất.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Đệ quy thử lần lượt từng separator theo thứ tự ưu tiên (`\n\n` → `\n` → `. ` → ` ` → `""`). **Base case**: nếu đoạn hiện tại đã `<= chunk_size` thì trả về nguyên đoạn (hoặc `[]` nếu rỗng); nếu đã thử hết separator mà vẫn còn dư thì hard-split cắt cứng theo `chunk_size`. Ở mỗi tầng đệ quy, tách văn bản theo separator hiện tại rồi gộp dần các phần lại thành một chunk cho tới khi vượt `chunk_size` thì chốt chunk hiện tại và mở chunk mới; nếu một phần đơn lẻ đã vượt `chunk_size` ngay từ đầu thì gọi đệ quy `_split` tiếp với separator kế tiếp trong danh sách.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` embed nội dung từng `Document` bằng `embedding_fn` rồi lưu dạng dict `{id, content, metadata, embedding}` vào list `self._store` (fallback in-memory khi không có ChromaDB) hoặc gọi `collection.add(...)` khi phát hiện có ChromaDB. `search` embed câu query, tính **tích vô hướng (dot product)** giữa vector query và từng vector đã lưu (vì các embedding đều được chuẩn hoá về norm 1 nên dot product tương đương cosine similarity), sắp xếp giảm dần theo score rồi lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` **lọc metadata TRƯỚC** (chỉ giữ lại record khớp tất cả cặp key/value trong `metadata_filter`), sau đó mới chạy similarity search trên tập đã lọc — tránh so sánh với các chunk chắc chắn không liên quan đến điều kiện lọc. `delete_document` xoá mọi record có `metadata['doc_id'] == doc_id` (tôi cho `_make_record` tự gán mặc định `metadata.setdefault("doc_id", doc.id)` để dùng được kể cả khi `Document` không set sẵn `doc_id` trong metadata), trả về `True` nếu kích thước store giảm sau khi xoá.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search(question, top_k)` để lấy các chunk liên quan nhất, nối nội dung các chunk thành một khối `context` (mỗi chunk một dòng gạch đầu dòng). Prompt được dựng theo cấu trúc: yêu cầu LLM **chỉ trả lời dựa trên context** được cung cấp (và nói rõ nếu không đủ thông tin), kèm theo `context` và câu hỏi gốc, cuối cùng gọi `llm_fn(prompt)` để sinh câu trả lời — đúng mô hình RAG: retrieve → build prompt → generate.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

Lệnh chạy (code nằm trong `src/NguyenCaoQuangAnh/`, không phải `src/` gốc):
```bash
LAB_SOLUTION_PACKAGE=src.NguyenCaoQuangAnh pytest tests/ -v
```

```
platform win32 -- Python 3.11.4, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker (7 tests) PASSED
tests/test_solution.py::TestSentenceChunker (4 tests) PASSED
tests/test_solution.py::TestRecursiveChunker (4 tests) PASSED
tests/test_solution.py::TestEmbeddingStore (8 tests) PASSED
tests/test_solution.py::TestKnowledgeBaseAgent (2 tests) PASSED
tests/test_solution.py::TestComputeSimilarity (4 tests) PASSED
tests/test_solution.py::TestCompareChunkingStrategies (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument (3 tests) PASSED

============================= 42 passed in 0.23s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Chạy `compute_similarity()` với **OpenAIEmbedder** (`text-embedding-3-small`, embedder thật, không dùng mock) trên 5 cặp câu trong chủ đề TMĐT/hỗ trợ khách hàng của K4.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Người mua có thể đổi trả sản phẩm trong 7 ngày nếu hàng lỗi." | "Khách hàng được hoàn trả hàng hóa trong vòng một tuần khi sản phẩm bị hư hỏng." | cao | 0.6353 | Đúng |
| 2 | "Người bán phải cung cấp thông tin sản phẩm chính xác." | "Hôm nay trời nắng đẹp, thích hợp để đi dạo công viên." | thấp | 0.2471 | Đúng |
| 3 | "Phí vận chuyển được tính dựa trên khối lượng đơn hàng." | "Giao hàng nhanh có thể phát sinh thêm phụ phí." | trung bình-cao | 0.5291 | Đúng |
| 4 | "Sản phẩm bị cấm không được đăng bán." | "Hàng cấm không được phép rao bán trên sàn." | rất cao | 0.6563 | Đúng |
| 5 | "Chính sách bảo mật quy định cách xử lý dữ liệu cá nhân của người dùng." | "Đội bóng đã giành chiến thắng trong trận đấu tối qua." | rất thấp | 0.2053 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 1 và cặp 4 có điểm khá gần nhau (0.6353 vs 0.6563) dù cặp 4 gần như là câu diễn giải lại 1-1 (near-paraphrase) còn cặp 1 diễn đạt lại theo cách tự nhiên hơn, dùng từ khác nhiều hơn ("7 ngày" ↔ "một tuần", "hàng lỗi" ↔ "sản phẩm bị hư hỏng"). Điều này cho thấy embedding không chỉ bắt sự trùng lặp từ vựng bề mặt mà thực sự mã hoá **ý nghĩa/khái niệm** (semantic), miễn là quan hệ ngữ nghĩa giữa các từ đồng nghĩa/diễn giải đủ mạnh trong dữ liệu huấn luyện của mô hình. Ngoài ra, không có cặp nào đạt cosine gần 1.0 dù là paraphrase khá sát — nhắc nhở rằng ngưỡng "cao/thấp" cần được hiệu chỉnh theo phân bố điểm thực tế của corpus, không nên kỳ vọng cứng một mốc tuyệt đối.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

> ⏳ **Chưa điền — cần đợi nhóm chốt xong 5 câu hỏi đánh giá (benchmark queries) và bộ tài liệu `data/k4_ecommerce/` đầy đủ (5–10 tài liệu thật) ở Giai đoạn 2.** Phần này bắt buộc chạy đúng 5 câu hỏi trùng với các thành viên trong nhóm (xem `REPORT_NHOM.md`).

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
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | __ / 10 (đợi Giai đoạn 2) |
| **Tổng phần cá nhân** | **50 / 60 (tạm tính)** |
