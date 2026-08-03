# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Đình Huy
**Nhóm:** A4-1
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau. Điều này thường cho thấy hai đoạn văn bản có nội dung, ngữ nghĩa hoặc chủ đề tương tự nhau, ngay cả khi chúng không sử dụng chính xác cùng một từ ngữ.

**Ví dụ có độ tương tự CAO:**
- Câu A: Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày sau khi nhận hàng.
- Câu B: Người mua được phép trả lại sản phẩm và nhận tiền hoàn lại trong 7 ngày kể từ ngày giao hàng.
- Tại sao tương đồng: Hai câu dùng cách diễn đạt khác nhau nhưng cùng nói về quyền đổi trả, hoàn tiền của người mua trong thời hạn 7 ngày.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Đơn hàng sẽ được giao đến khách hàng trong vòng ba ngày làm việc.
- Câu B: Python là một ngôn ngữ lập trình được sử dụng phổ biến trong khoa học dữ liệu.
- Tại sao khác: Câu A nói về thời gian giao hàng trong thương mại điện tử, còn câu B nói về ngôn ngữ lập trình nên nội dung và chủ đề hầu như không liên quan.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào góc, tức hướng của hai vector, thay vì độ lớn của chúng. Vì vậy, nó phù hợp để so sánh ngữ nghĩa của văn bản và ít bị ảnh hưởng bởi độ dài văn bản hoặc độ lớn của vector hơn khoảng cách Euclid.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: `ceil((độ_dài_tài_liệu - overlap) / (chunk_size - overlap))`.
>
> Thay số: `ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.111...) = 23`.
>
> **Đáp án: 23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi `overlap=100`, số chunk là `ceil((10,000 - 100) / (500 - 100)) = ceil(9,900 / 400) = ceil(24.75) = 25`, tức tăng từ 23 lên 25 chunks. Overlap lớn hơn giúp giữ lại nhiều ngữ cảnh ở ranh giới giữa hai chunk, hạn chế việc một ý hoặc một câu quan trọng bị chia cắt; đổi lại, hệ thống phải lưu trữ và xử lý nhiều dữ liệu trùng lặp hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng biểu thức chính quy `(?<=[.!?])(?:[ \t]+|\r?\n+)` để tách tại khoảng trắng hoặc xuống dòng đứng sau các dấu kết thúc câu `.`, `!`, `?`, đồng thời vẫn giữ dấu câu trong nội dung. Sau khi loại bỏ khoảng trắng và các phần rỗng, các câu được gom theo từng nhóm không vượt quá `max_sentences_per_chunk`. Nếu đầu vào rỗng hoặc chỉ chứa khoảng trắng, hàm trả về danh sách rỗng; tham số số câu cũng luôn được giới hạn tối thiểu là 1.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử các separator theo thứ tự ưu tiên từ cấu trúc lớn đến nhỏ: đoạn văn, dòng, câu, từ và cuối cùng là chuỗi rỗng. Mỗi lần chia, tôi ghép lại các phần nhỏ nếu tổng độ dài chưa vượt `chunk_size`; phần vẫn quá dài sẽ được xử lý đệ quy bằng separator tiếp theo, đồng thời separator được gắn lại để không làm mất dấu câu hoặc ranh giới đoạn. Trường hợp cơ sở là đoạn hiện tại đã không vượt quá `chunk_size`; nếu hết separator, hàm cắt trực tiếp thành các lát có kích thước cố định để bảo đảm thuật toán luôn kết thúc.

**`compute_similarity` + `ChunkingStrategyComparator.compare`** — hướng tiếp cận:
> `compute_similarity` tính tích vô hướng rồi chia cho tích độ lớn của hai vector; hàm trả về `0.0` nếu một vector có độ lớn bằng 0 và báo lỗi nếu hai vector khác số chiều. Comparator chạy cùng văn bản qua `FixedSizeChunker`, `SentenceChunker` và `RecursiveChunker`, sau đó trả về danh sách chunk, số lượng chunk và độ dài trung bình của từng chiến lược để có thể so sánh.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Khi thêm tài liệu, tôi sao chép metadata, tự bổ sung `doc_id` nếu chưa có, tạo embedding từ nội dung và lưu thành record gồm ID duy nhất, nội dung, metadata và vector. Store luôn duy trì bản lưu trong bộ nhớ để hoạt động ổn định; nếu ChromaDB có sẵn thì dữ liệu cũng được ghi vào một collection tạm thời, còn lỗi khởi tạo hoặc ghi ChromaDB sẽ tự động chuyển về in-memory. Khi tìm kiếm, câu truy vấn được embedding một lần, tính dot product với từng vector, sắp xếp score giảm dần và trả về tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Với `search_with_filter`, tôi lọc record theo metadata trước rồi mới tính độ tương tự, nhờ vậy các kết quả ngoài phạm vi không tham gia xếp hạng; nếu không truyền bộ lọc thì hàm hoạt động giống `search`. `delete_document` tìm tất cả record có `metadata["doc_id"]` trùng với ID yêu cầu và xóa toàn bộ các chunk đó ở cả bộ nhớ lẫn ChromaDB. Hàm trả về `True` nếu có dữ liệu bị xóa và `False` nếu không tìm thấy tài liệu.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm `answer` trước tiên dùng câu hỏi để lấy tối đa `top_k` chunk liên quan từ `EmbeddingStore`, đánh số từng tài liệu rồi ghép chúng vào phần `NGỮ CẢNH` của prompt. Prompt gồm hướng dẫn chỉ sử dụng thông tin trong ngữ cảnh, phần câu hỏi và vị trí dành cho câu trả lời; nếu không truy xuất được chunk nào, prompt nói rõ rằng cơ sở tri thức không có tài liệu liên quan. Prompt hoàn chỉnh được truyền vào `llm_fn` và kết quả của mô hình được trả về cho người dùng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi ghi dự đoán trước khi chạy và dùng model đa ngữ `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` để tạo embedding. Điểm thực tế được tính bằng hàm `compute_similarity()` đã triển khai; tôi quy ước mức cao từ `0.60` trở lên, mức thấp dưới `0.40`, còn khoảng giữa là mức trung bình.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày sau khi nhận hàng. | Người mua được phép trả lại sản phẩm và nhận tiền hoàn lại trong 7 ngày kể từ ngày giao hàng. | Cao | 0.795304 | Có |
| 2 | Đơn hàng sẽ được giao trong vòng ba ngày làm việc. | Thời gian vận chuyển dự kiến của đơn hàng là ba ngày làm việc. | Cao | 0.880231 | Có |
| 3 | Chính sách đổi trả cho phép khách hàng hoàn lại sản phẩm bị lỗi. | Python là một ngôn ngữ lập trình phổ biến trong khoa học dữ liệu. | Thấp | 0.015161 | Có |
| 4 | Người bán phải cung cấp hóa đơn cho người mua. | Người bán không cần cung cấp hóa đơn cho người mua. | Thấp | 0.475419 | Không (điểm trung bình) |
| 5 | Người mua có thể hủy đơn hàng trước khi sản phẩm được giao. | The buyer can cancel the order before the product is delivered. | Cao | 0.890237 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là cặp 4: hai câu trái nghĩa do cụm “phải” và “không cần”, nhưng vẫn đạt `0.475419` vì phần lớn từ vựng và cấu trúc câu giống nhau. Điều này cho thấy embedding có thể nhận diện tốt chủ đề tổng quát nhưng chưa chắc biểu diễn chính xác phủ định hoặc nghĩa vụ; vì vậy score tương đồng cao hoặc trung bình không đồng nghĩa với việc hai câu hoàn toàn cùng ý. Cặp 5 cũng cho thấy model đa ngữ có thể đặt hai câu Việt–Anh cùng nghĩa rất gần nhau trong không gian vector.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`). Chiến lược: `RecursiveChunker(chunk_size=500)`, corpus chung `data/k4_ecommerce/` (5 tài liệu Shopee + Tiki), OpenAI embedder thật (`text-embedding-3-small`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Điều kiện trả hàng/hoàn tiền (filter `customer_role=buyer`) | "3.2. Người Mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 ngày kể từ lúc giao hàng thành công..." | 0.6994 | Có, top-1 | Trích đúng thời hạn 15 ngày |
| 2 | Quy định pháp luật cho người bán (filter `customer_role=seller`) | "b. Khi đăng bán sản phẩm... tuân thủ Điều 117, Điều 120.4, Điều 121 Luật Thương Mại..." | 0.7416 | Có, top-1 | Trích đúng các điều luật |
| 3 | Phương thức thanh toán Shopee chấp nhận | "V. Quy trình thanh toán..." + chunk về thẻ Visa/Master/JCB/AMEX | 0.7244 | Có, top-1/2 | Nêu đúng phương thức thanh toán |
| 4 | Danh sách hàng cấm gồm nhóm nào | "g. Thành viên không được... gây mất uy tín Sàn..." (quy định thành viên, không phải danh sách hàng cấm) | 0.6465 | **Không** | Lạc đề — chunk gần nhất chỉ nhắc "Danh sách sản phẩm bị cấm/hạn chế" mà không liệt kê |
| 5 | Quy trình giải quyết tranh chấp gồm mấy bước | "Phân định trách nhiệm giải quyết tranh chấp: tranh chấp giữa người dùng → tự thỏa thuận/hòa giải..." | 0.7068 | Có liên quan, nhưng không nêu đúng số bước cụ thể | Liên quan chủ đề nhưng chưa trả lời đúng "mấy bước" |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5 (câu 4 miss)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> `RecursiveChunker(500)` của tôi cho kết quả rất tốt ở câu 1–3 (trúng thẳng chi tiết cụ thể như số ngày, tên điều luật) — ngang bằng hoặc tốt hơn cả chiến lược heading-based của Quang Anh ở các câu này. Tuy nhiên chunk 500 ký tự không giữ được tiêu đề Mục cha, nên bị lạc đề ở câu 4 (danh sách hàng cấm) — trong khi `SentenceChunker` của Tuấn Minh và `SectionAwareChunker` (bản cải tiến của Quang Anh, có gắn tiêu đề Mục vào chunk) đều trúng câu này. Bài học: chunk nhỏ tốt cho việc bám sát dữ kiện cụ thể, nhưng cần thêm cơ chế giữ ngữ cảnh chủ đề (heading) để không lạc đề với các mục liệt kê dài.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 7 / 10 (4/5 câu top-1 đúng, câu 4 miss) |
| **Tổng phần cá nhân** | **(các mục 1-4 tự điền) + 7/10 ở Mục 5** |
