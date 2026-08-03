# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Tuấn Minh
**Nhóm:** K4-A4-1
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Khi hai đoạn văn bản có ý nghĩa gần giống nhau, vector embedding của chúng sẽ hướng gần nhau trong không gian nhiều chiều, dẫn đến cosine similarity cao.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Đổi trả hàng trong vòng 7 ngày nếu sản phẩm bị lỗi."
- Câu B: "Khách hàng có thể hoàn lại sản phẩm trong 7 ngày nếu sản phẩm hỏng."
- Tại sao tương đồng: cả hai nói về cùng một quy định đổi trả trong thời gian cụ thể.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Đổi trả hàng trong vòng 7 ngày nếu sản phẩm bị lỗi."
- Câu B: "Hôm nay trời rất đẹp và nắng nóng."
- Tại sao khác: nội dung mang ý nghĩa hoàn toàn khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector, phù hợp hơn khi so sánh ý nghĩa ngữ nghĩa, trong khi khoảng cách Euclid bị ảnh hưởng nhiều bởi độ lớn của vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Số chunk được tính bằng công thức: ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23 chunks.
> **Đáp án:** 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, bước dịch chuyển sẽ giảm từ 450 xuống 400, nên số chunk sẽ tăng lên. Độ chồng chéo nhiều hơn giúp giữ ngữ cảnh liên tục giữa các chunk, đặc biệt hữu ích cho retrieval khi câu hoặc ý nghĩa bị cắt giữa các chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex để tách văn bản theo các ranh giới câu như dấu chấm, chấm than và chấm hỏi, sau đó gom các câu thành từng chunk theo số câu tối đa. Nếu văn bản rỗng hoặc không có câu nào, hàm trả về danh sách rỗng để tránh lỗi.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử chia theo các separator theo thứ tự ưu tiên như đoạn văn, xuống dòng, dấu chấm, khoảng trắng. Khi một đoạn vẫn quá dài, hàm sẽ đệ quy tiếp với separator tiếp theo cho đến khi đạt kích thước chunk mong muốn. Trường hợp cơ sở là khi đoạn văn bản đã ngắn hơn hoặc bằng kích thước chunk thì dừng lại.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi tài liệu được chuyển thành một record bao gồm `doc_id`, nội dung, metadata và embedding. Khi search, câu hỏi được nhúng rồi so sánh với các embedding đã lưu bằng dot product để xếp hạng độ liên quan.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc các record theo metadata trước rồi mới thực hiện tìm kiếm trên tập đã lọc, giúp giảm nhiễu và tăng độ chính xác. `delete_document` loại bỏ tất cả các chunk có cùng `doc_id` để tránh dữ liệu thừa sau khi xóa tài liệu.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm lấy top-k chunk liên quan nhất từ store, ghép thành một prompt có phần ngữ cảnh và gửi cho LLM giả lập để tạo câu trả lời. Cách này áp dụng mẫu RAG cơ bản: truy xuất trước, rồi dùng retrieved context để trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
py -3 -m pytest tests/ -v
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0, py-3
collected 42 items

42 passed in 0.13s
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Đổi trả trong 7 ngày" | "Có thể đổi trả sản phẩm trong vòng 7 ngày" | cao | cao | Có |
| 2 | "Thanh toán bằng thẻ" | "Sản phẩm bị lỗi" | thấp | thấp | Có |
| 3 | "Giao hàng chậm" | "Đơn hàng đến muộn" | cao | cao | Có |
| 4 | "Chính sách bảo mật" | "Quyền riêng tư dữ liệu" | cao | cao | Có |
| 5 | "Mua sắm online" | "Trời hôm nay đẹp" | thấp | thấp | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điều bất ngờ nhất là các câu có cùng ý nghĩa nhưng khác từ ngữ vẫn có thể có similarity cao. Điều này cho thấy embeddings không chỉ phụ thuộc vào từ giống nhau mà còn nắm được mối liên hệ ngữ nghĩa và ngữ cảnh.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`). Chiến lược: `SentenceChunker(max_sentences_per_chunk=3)`, corpus chung `data/k4_ecommerce/` (5 tài liệu Shopee + Tiki), OpenAI embedder thật.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Điều kiện trả hàng/hoàn tiền (filter `customer_role=buyer`) | "3.2. Người Mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 ngày..." | 0.6997 | Có, top-1 | Trích đúng thời hạn 15 ngày |
| 2 | Quy định pháp luật cho người bán (filter `customer_role=seller`) | "b. Khi đăng bán sản phẩm... tuân thủ Điều 117, 120.4, 121 Luật Thương Mại..." | 0.7411 | Có, top-1 | Trích đúng các điều luật |
| 3 | Phương thức thanh toán Shopee chấp nhận | "V. Quy trình thanh toán Người Mua và Người Bán có thể tham khảo..." | 0.7562 | Có, top-1 | Nêu đúng phương thức thanh toán |
| 4 | Danh sách hàng cấm gồm nhóm nào | "Danh sách sản phẩm cấm giao dịch... 2.1. Hàng vi phạm bản quyền..." | **0.7045** | **Có, top-1 — duy nhất trong cả nhóm (lúc đó) trúng thẳng câu này** | Xác định đúng, trích được nhóm đầu tiên |
| 5 | Quy trình giải quyết tranh chấp gồm mấy bước | "Tùy vào thỏa thuận giữa Người Mua và Người Bán mà Shopee có thể hỗ trợ..." | 0.6784 | Có liên quan nhưng chưa nêu đúng số bước cụ thể | Liên quan chủ đề, chưa trả lời chính xác "mấy bước" |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 (4 câu top-1 chính xác, câu 5 liên quan nhưng chưa chính xác tuyệt đối)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được rằng chiến lược chunking và metadata có ảnh hưởng rất lớn đến chất lượng retrieval. Một số bạn dùng chunk ngắn và có metadata lọc tốt, nên câu hỏi cụ thể trả về kết quả tốt hơn so với cách chunk quá dài hoặc thiếu thông tin ngữ cảnh. Kết quả thực tế xác nhận điều này: `SentenceChunker` (chunk rất nhỏ, 3 câu) là chiến lược **duy nhất** trong nhóm trúng đích câu 4 (danh sách hàng cấm) ở lần chạy đầu tiên — vì chunk nhỏ tình cờ giữ trọn câu tiêu đề "Danh sách sản phẩm cấm giao dịch" cùng với nhóm đầu tiên trong cùng 1 chunk, trong khi các chunk lớn hơn (Recursive 500, Heading 2000) lại pha loãng tín hiệu này với nội dung xung quanh.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 (5/5 câu liên quan trong top-3, 4/5 chính xác tuyệt đối ở top-1 — điểm cao nhất nhóm, đã chạy thật thay vì điểm ước tính trước đó) |
| **Tổng phần cá nhân** | **59 / 60** |
