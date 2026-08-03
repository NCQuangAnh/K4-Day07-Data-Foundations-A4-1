# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Quang Trung (MSSV: 2A202601158)  
**Nhóm:** A4-1 
**Ngày:** 03/08/2026

> Báo cáo này ghi nhận phần triển khai cá nhân trong `src/`. Phần đánh giá truy xuất ở Mục 5 dùng corpus khởi động của lab và mock embedding, nên chỉ là kiểm tra kỹ thuật; không thay thế benchmark 5 câu hỏi và corpus nguồn công khai do nhóm thống nhất.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**  
Cosine cao nghĩa là hai vector embedding có hướng gần nhau; với một embedding ngữ nghĩa tốt, hai đoạn văn thường đang nói về các ý gần nhau. Chỉ số này không khẳng định hai câu giống hệt nhau, mà đo sự tương đồng về hướng biểu diễn.

**Ví dụ có độ tương tự CAO:**

- Câu A: “Người mua có thể yêu cầu đổi trả khi hàng bị lỗi.”
- Câu B: “Khách hàng cần gửi yêu cầu hoàn trả cho sản phẩm bị lỗi.”
- Tại sao tương đồng: Cả hai đều nói về hành động đổi trả/hoàn trả khi sản phẩm có lỗi.

**Ví dụ có độ tương tự THẤP:**

- Câu A: “Người bán phải mô tả sản phẩm chính xác.”
- Câu B: “Dự báo thời tiết hôm nay có mưa.”
- Tại sao khác: Hai câu đề cập hai chủ đề không liên quan: quy định đăng bán và thời tiết.

**Tại sao độ tương tự cosine được ưu tiên hơn khoảng cách Euclid cho text embeddings?**  
Độ dài vector có thể thay đổi do đặc tính mô hình hoặc độ dài văn bản, trong khi cosine tập trung vào hướng của vector — phần thường mang tín hiệu ngữ nghĩa. Vì vậy cosine phù hợp hơn khi cần xếp hạng mức liên quan giữa truy vấn và các đoạn văn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**

\[
\left\lceil\frac{10.000 - 50}{500 - 50}\right\rceil
= \left\lceil\frac{9.950}{450}\right\rceil
= 23
\]

**Đáp án:** 23 chunks.

**Nếu overlap tăng lên 100 thì sao?**  
Số chunk là \(\lceil(10.000-100)/(500-100)\rceil = \lceil9.900/400\rceil = 25\), nên tăng thêm 2 chunks. Overlap lớn hơn giữ được ngữ cảnh ở ranh giới giữa hai chunk, nhưng làm tăng số vector cần lưu và khả năng trả về nội dung trùng lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` — hướng tiếp cận:**  
Tôi dùng regex `(?<=[.!?])(?:\s+)` để cắt sau dấu kết thúc câu và giữ dấu câu trong câu đứng trước. Sau khi loại chuỗi rỗng/chuỗi chỉ có khoảng trắng, các câu được gom theo `max_sentences_per_chunk`; tham số này luôn được chặn tối thiểu là 1.

**`RecursiveChunker.chunk` / `_split` — hướng tiếp cận:**  
Thuật toán ưu tiên lần lượt `\n\n`, `\n`, `. `, khoảng trắng rồi đến tách theo ký tự khi không còn separator phù hợp. Trường hợp cơ sở là đoạn không dài hơn `chunk_size`; đoạn dài hơn được tách đệ quy bằng separator có ưu tiên thấp hơn, rồi ghép tham lam các mảnh vừa kích thước để giảm số chunk và vẫn giữ separator.

### Lớp `EmbeddingStore`

**`add_documents` + `search` — hướng tiếp cận:**  
Mỗi `Document` được chuẩn hóa thành record gồm `id`, `content`, `metadata`, embedding và một `record_id` nội bộ duy nhất. Store thử sử dụng ChromaDB nếu môi trường có hỗ trợ, đồng thời giữ cache in-memory để fallback ổn định; truy vấn được embedding và xếp hạng giảm dần theo tích vô hướng. Với mock embedder đã chuẩn hóa vector, tích vô hướng tương đương cosine similarity.

**`search_with_filter` + `delete_document` — hướng tiếp cận:**  
`search_with_filter` lọc metadata trước bằng điều kiện khớp toàn bộ cặp khóa–giá trị, rồi chỉ xếp hạng các record còn lại. Khi thêm document, tôi mặc định gắn `metadata["doc_id"]` nếu chưa có; `delete_document` dựa vào trường này để xóa toàn bộ chunk cùng tài liệu và trả về trạng thái thành công.

### Tác tử `KnowledgeBaseAgent`

**`answer` — hướng tiếp cận:**  
Agent lấy top-k chunk từ store, đánh số từng chunk và ghép chúng vào phần `Context` của prompt. Prompt yêu cầu LLM chỉ dùng ngữ cảnh được cấp, nêu rõ khi dữ liệu không đủ, sau đó đưa `Question` và gọi `llm_fn` để nhận câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

Đã chạy bộ kiểm thử tương thích `unittest` từ thư mục gốc của lab:

```text
python -m unittest discover -s tests -v

Ran 42 tests in 0.011s
OK
```

**Số lượng bài test vượt qua:** **42 / 42**.

Các kiểm thử bao phủ ba chunker, cosine similarity, thêm/tìm/lọc/xóa trong `EmbeddingStore`, và luồng trả lời cơ bản của `KnowledgeBaseAgent`.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Các số dưới đây được tính bằng `compute_similarity(_mock_embed(A), _mock_embed(B))`. Mock embedder là deterministic nhưng gần như ngẫu nhiên theo toàn bộ chuỗi, nên dùng để kiểm tra hàm chứ không dùng để kết luận chất lượng ngữ nghĩa.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Người mua muốn đổi trả sản phẩm bị lỗi. | Khách hàng cần gửi yêu cầu hoàn trả khi hàng bị lỗi. | Cao | 0.1203 | Không |
| 2 | Người bán phải mô tả sản phẩm chính xác. | Thông tin giá và tình trạng hàng phải chính xác. | Cao | 0.0413 | Không |
| 3 | Chính sách đổi trả yêu cầu bằng chứng phù hợp. | Khách hàng cần cung cấp bằng chứng khi sản phẩm sai mô tả. | Cao | -0.1479 | Không |
| 4 | Người bán đăng sản phẩm. | Người mua yêu cầu đổi trả hàng. | Thấp | -0.0169 | Có |
| 5 | Thời tiết hôm nay có mưa không? | Người bán phải cung cấp giá sản phẩm. | Thấp | 0.1040 | Có |

**Kết quả bất ngờ nhất và ý nghĩa:**  
Ba cặp có ý nghĩa gần nhau đều không đạt điểm cao, thậm chí cặp 3 có điểm âm. Điều này phù hợp với lưu ý của README: mock embedding chỉ phục vụ unit test. Để so sánh retrieval thật, cần dùng `EMBEDDING_PROVIDER=local` với embedding đa ngôn ngữ hoặc một backend embedding thật khác.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Thiết lập thử nghiệm

- Corpus: `data/k4_ecommerce/` gồm 2 tài liệu khởi động, được chia thành 3 chunk với `FixedSizeChunker(chunk_size=500, overlap=50)`.
- Embedder: `_mock_embed`.
- Agent: hàm demo chỉ xác nhận prompt nhận được context, không phải LLM dùng để chấm độ đúng của câu trả lời.

> Hai tài liệu hiện tại đều ghi rõ là template, với `source_url` dạng `example.com`; do đó chúng chưa đủ điều kiện thay thế corpus 5–10 nguồn công khai của nhóm. Bảng này là kiểm tra hành vi `search`/`KnowledgeBaseAgent`, không phải kết quả benchmark cuối cùng.

| # | Câu hỏi (Query) | Top-1 chunk truy xuất được (tóm tắt) | Điểm score | Có chunk liên quan trong top-3? | Câu trả lời của Agent (tóm tắt) |
|---|---|---|---:|---|---|
| 1 | Người mua cần làm gì để đổi trả hàng bị lỗi? | Chunk thuộc tài liệu đổi trả, nhưng chủ yếu là phần metadata template. | 0.1560 | Có, tài liệu đổi trả xuất hiện trong top-3. | Prompt nhận context; demo LLM không tổng hợp câu trả lời. |
| 2 | Yêu cầu đổi trả cần kèm theo gì? | Chunk metadata của tài liệu đổi trả. | -0.0366 | Có, chunk nội dung đổi trả xuất hiện trong top-3. | Prompt nhận context; cần LLM thật để đánh giá câu trả lời. |
| 3 | Người bán có trách nhiệm gì khi hàng bị lỗi? | Chunk đổi trả nêu người bán phản hồi theo quy trình của sàn. | 0.1689 | Có. | Prompt nhận context; có thể trả lời khi thay demo bằng LLM. |
| 4 | Người bán phải cung cấp thông tin nào khi đăng sản phẩm? | Chunk đổi trả, không phải chunk đăng bán tốt nhất. | -0.0743 | Có, vì corpus chỉ có 3 chunk và chunk đăng bán nằm trong top-3. | Prompt nhận context; top-1 chưa phù hợp để trả lời tin cậy. |
| 5 | Sản phẩm nào không được đăng bán? | Chunk đổi trả, không phải nội dung cấm/hạn chế đăng bán. | 0.0750 | Có, chunk đăng bán nằm trong top-3. | Prompt nhận context; top-1 chưa phù hợp để trả lời tin cậy. |

**Bao nhiêu câu hỏi có chunk thuộc tài liệu liên quan trong top-3?** **5 / 5**.  
Con số này không thể hiện retrieval tốt vì toàn bộ corpus chỉ có 3 chunk và truy vấn `top_k=3` trả về toàn bộ corpus. Kết quả top-1 ở câu 4 và 5 cho thấy mock embedding không phù hợp để đánh giá ngữ nghĩa.

**Điều học được từ hướng dẫn lab và lần chạy thử:**  
Chất lượng corpus và embedding có ảnh hưởng trực tiếp đến kết quả hơn việc chỉ “có vector store”. Với dữ liệu thật, metadata như `customer_role` và `category` nên được dùng để thu hẹp ứng viên trước khi tìm kiếm; đồng thời cần đánh giá cả top-1 lẫn top-3 để phát hiện trường hợp top-k có thông tin đúng nhưng thứ hạng chưa tốt.

---

## Tự đánh giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 2 / 10 (tạm thời) |
| **Tổng phần cá nhân** | **52 / 60 (tạm thời)** |

> Để hoàn tất Mục 5 theo đúng yêu cầu chấm điểm, nhóm cần bổ sung 5–10 tài liệu nguồn công khai, thống nhất đúng 5 benchmark query + gold answer trong `REPORT_NHOM.md`, dùng local multilingual embedder và chạy lại bảng kết quả.
