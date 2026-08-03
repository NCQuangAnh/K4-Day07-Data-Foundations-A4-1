# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** A4-2
**Thành viên:** Nguyễn Cao Quang Anh, Vũ Đình Huy, Lê Tuấn Minh, Nguyễn Thị Nam Phương, Lê Quang Trung
**Ngày:** 2026-08-03 (cập nhật lần cuối)

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:** Quy chế hoạt động và các chính sách vận hành trên nền tảng TMĐT (Shopee + Tiki) — bao gồm quy chế tổng quát (2 phiên bản Shopee để so sánh tính mới), chính sách trả hàng/hoàn tiền (buyer), quy định đăng bán sản phẩm (seller), và chính sách phí bán hàng (seller, nền tảng khác — Tiki) để tăng đa dạng nguồn.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy chế hoạt động Sàn TMĐT Shopee.vn (2025) | help.shopee.vn/portal/4/article/77245 | 2026-08-03 / hiệu lực 2025-01-03 | 103.267 | doc_id, title, source_url, retrieved_at, document_version, customer_role=both, category=platform-rules, language=vi |
| 2 | Quy chế hoạt động Sàn TMĐT Shopee.vn (2022, đã hết hiệu lực) | shopee.vn/docs/170 (bản PDF do thành viên cung cấp) | 2026-08-03 / hiệu lực 2022-08-05 | 22.544 | như trên, giữ lại có chủ đích để so sánh độ mới tài liệu |
| 3 | Chính sách trả hàng và hoàn tiền Shopee | help.shopee.vn/portal/4/article/77251 | 2026-08-03 / not-stated | 26.485 | customer_role=buyer, category=returns |
| 4 | Quy định về đăng bán sản phẩm trên Shopee | help.shopee.vn/portal/4/article/77246 | 2026-08-03 / not-stated | 29.362 | customer_role=seller, category=listing |
| 5 | Chính sách Phí & Biểu phí SGD TMĐT Tiki (02-QĐCS-MP) | salt.tikicdn.com/ts/sellercenterFE/.../....pdf | 2026-08-03 / phiên bản 26.25, hiệu lực 2024-05-06 | 4.830 | customer_role=seller, category=fees |

> Ghi chú: nhóm chủ đích giữ **2 phiên bản Quy chế** (2022 và 2025) trong cùng corpus — đây là chất liệu cho phần Phân tích lỗi (Bài 3.5): nếu không lọc theo `document_version`/`retrieved_at`, truy xuất có thể trả về chunk từ bản đã hết hiệu lực. Tài liệu Tiki (#5) được thêm để corpus không chỉ đến từ một nền tảng duy nhất, đồng thời bổ sung `category=fees` chưa có trước đó.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | string (buyer/seller/both) | `buyer` | Lọc trước khi tìm kiếm ngữ nghĩa — loại bỏ nhiễu từ tài liệu không liên quan đến vai trò người hỏi (K4 bắt buộc) |
| `category` | string | `returns`, `listing`, `platform-rules` | Thu hẹp phạm vi tìm kiếm theo chủ đề cụ thể khi câu hỏi đã rõ lĩnh vực |
| `document_version` / `retrieved_at` | string (ngày/phiên bản) | `2025-01-03` | Ưu tiên/loại trừ tài liệu đã hết hiệu lực — kiểm tra độ mới của thông tin trước khi tin câu trả lời |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=500)` trên 2 tài liệu (embedder không cần thiết ở bước này, chỉ so thống kê chunk):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Chính sách trả hàng/hoàn tiền | FixedSizeChunker (`fixed_size`) | 40 | 499.3 | Không — cắt cứng theo ký tự, có thể chia đôi 1 câu/điều khoản |
| Chính sách trả hàng/hoàn tiền | SentenceChunker (`by_sentences`) | 48 | 413.2 | Giữ trọn câu nhưng có thể tách rời các câu cùng một ý (VD: từng điều kiện trong danh sách liệt kê) |
| Chính sách trả hàng/hoàn tiền | RecursiveChunker (`recursive`) | 62 | 320.2 | Tốt hơn ở ranh giới đoạn/câu nhưng vẫn cắt ngang các mục con (1.1, 1.2…) khi đoạn dài |
| Quy định đăng bán sản phẩm | FixedSizeChunker (`fixed_size`) | 44 | 498.0 | Không — tương tự trên |
| Quy định đăng bán sản phẩm | SentenceChunker (`by_sentences`) | 79 | 274.5 | Vỡ vụn nhiều hơn do văn bản có nhiều câu ngắn dạng liệt kê |
| Quy định đăng bán sản phẩm | RecursiveChunker (`recursive`) | 54 | 403.9 | Giữ đoạn văn tốt hơn `by_sentences` nhưng chưa bám theo cấu trúc heading pháp lý (A., B., 1., 2., a., b.) |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Cao Quang Anh**
- **Loại chiến lược:** Custom — `HeadingChunker`, sau đó cải tiến thành `SectionAwareChunker` (`src/NguyenCaoQuangAnh/heading_chunker.py`)
- **Mô tả & lý do chọn cho chủ đề này:** Văn bản quy chế/chính sách TMĐT có cấu trúc heading La Mã cấp cao rõ ràng (I., II., III.,...), mỗi mục là một điều khoản trọn vẹn về ý nghĩa. `HeadingChunker` (bản đầu) tách theo các heading này, mục nào quá dài (vd. danh sách hàng cấm) được chia tiếp bằng `RecursiveChunker(chunk_size=2000)`.
- **Cải tiến sau khi phân tích lỗi (câu 5):** phát hiện các heading phụ dạng số Ả Rập (vd. "6. Quy trình giải quyết tranh chấp") nằm bên trong 1 mục La Mã bị tách rời khỏi nội dung của chính nó khi fallback qua `RecursiveChunker`, khiến chunk mất ngữ cảnh chủ đề và dễ nhầm với quy trình khác có cùng khuôn mẫu "Bước 1, 2, 3...". `SectionAwareChunker` tách thêm theo heading phụ này và **luôn giữ dòng tiêu đề (La Mã + số) dính vào đầu mỗi chunk con** (vd. `"III. Quy trình giao dịch... | 6. Quy trình giải quyết tranh chấp/Xử lý khiếu nại"`) để vector "nhớ" đúng chủ đề dù chunk nhỏ.
- **Kết quả cải tiến (chạy thật, `max_chunk_size=1200`, 178 chunk):** Câu 4 (danh sách hàng cấm) → **top-1 trúng thẳng** (0.6508, tốt hơn cả `SentenceChunker` của Tuấn Minh). Câu 5 (quy trình tranh chấp) → chunk đúng chủ đề `"III... | 6. Quy trình giải quyết tranh chấp"` **lần đầu xuất hiện trong top-3** (hạng 3, 0.6620) — trước đó không chiến lược nào trong nhóm có chunk đúng chủ đề lọt top-3. Chưa lên được hạng 1 nên câu 5 vẫn chỉ đạt 1/2 điểm theo rubric, nhưng đã cải thiện từ "miss hẳn" (0đ) lên "có liên quan trong top-3" (1đ).
- **Code:** xem `src/NguyenCaoQuangAnh/heading_chunker.py` (`HeadingChunker` + `SectionAwareChunker`); script so sánh: `scripts/phase2_benchmark.py`.

**Thành viên 2 — Vũ Đình Huy**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=500)` (một trong 3 chiến lược có sẵn, chưa có custom riêng)
- **Mô tả & lý do chọn:** Implement `RecursiveChunker` thử tách theo từng cấp separator (đoạn văn → dòng → câu → khoảng trắng), gộp tham lam các phần nhỏ cho tới gần `chunk_size`; phần quá dài mới đệ quy sang separator ưu tiên thấp hơn. Đây là chiến lược có cấu trúc rõ ràng, phù hợp làm cơ sở so sánh chung với các thành viên khác dùng cùng loại chunker.
- **Code:** `src/VuDinhHuy/chunking.py`.

**Thành viên 3 — Nguyễn Thị Nam Phương**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=500)`
- **Mô tả & lý do chọn:** Dùng cách tiếp cận đệ quy theo separator ưu tiên (đoạn văn → dòng → câu → khoảng trắng), gộp các phần nhỏ lại gần `chunk_size` trước khi cắt tiếp. Đây là chiến lược có sẵn phù hợp làm điểm so sánh chung với Huy và Trung (cùng dùng `RecursiveChunker`).
- **Code:** `src/NguyenThiNamPhuong/chunking.py`.

**Thành viên 4 — Lê Quang Trung**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=500)` (implement trực tiếp trong `src/chunking.py`, `src/store.py`, `src/agent.py` gốc theo đúng hướng dẫn README, không dùng folder cá nhân)
- **Mô tả & lý do chọn:** Cùng thuật toán đệ quy theo separator ưu tiên như Huy và Phương, viết trực tiếp vào package `src` gốc thay vì tạo bản sao riêng.
- **Code:** nhánh `trunglq`, `src/chunking.py` (root).

**Thành viên 5 — Lê Tuấn Minh**
- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=3)`
- **Mô tả & lý do chọn:** Tách câu theo dấu kết thúc câu, gộp mỗi 3 câu thành 1 chunk. Tuấn Minh chọn chiến lược này vì cho rằng "mỗi câu thường mang ý nghĩa rõ ràng nên dễ truy xuất hơn" với văn bản chính sách.
- **Code:** `src/2A202601390-LeTuanMinh/chunking.py`.



### So Sánh Giữa Các Thành Viên

> Chạy `scripts/phase2_benchmark.py` với **OpenAI embedder thật** (`text-embedding-3-small`) trên toàn bộ 5 tài liệu (đã thêm Tiki). Quang Anh có 3 vòng thử: `FixedSizeChunker` (baseline) → `HeadingChunker` (custom v1) → `SectionAwareChunker(max_chunk_size=400)` (custom v2, cải tiến sau khi phân tích lỗi).

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10)\* | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Quang Anh | FixedSizeChunker (baseline, 315 chunk) | 5/10 (2.5/5 câu rõ ràng đúng) | Chunk nhỏ → nhiều ứng viên, đôi khi 1 fact ngắn (vd. "Visa, Master Card JCB") lọt vào top-3 | Cắt cứng theo ký tự nên hay xé lẻ một điều khoản/danh sách ra nhiều mảnh rời rạc, không có chunk nào "đủ" để trả lời trọn vẹn |
| Quang Anh | HeadingChunker (custom v1, 87 chunk, max_chunk_size=2000) | 7/10 (3.5/5 câu rõ ràng đúng) | Chunk lớn hơn, bám theo điều khoản thật → nhiều khả năng 1 chunk chứa trọn câu trả lời (rõ nhất ở câu 1, 2, 3) | Chunk quá lớn (2000 ký tự) đôi khi lẫn cả phần mở đầu ít liên quan; câu 4, 5 vẫn miss |
| **Quang Anh** | **SectionAwareChunker (custom v2, 537 chunk, max_chunk_size=400)** | **9/10** (4/5 câu top-1 trúng đích) | Kết hợp cả 2 điểm mạnh: chunk nhỏ (400 ký tự, như Recursive/Sentence) **và** luôn giữ tiêu đề Mục dính vào đầu chunk (như v1). Trúng top-1 rõ ràng ở câu 1 (0.7056), câu 2 (0.7366), câu 3 (0.7304), và **câu 4 đạt điểm cao nhất trong toàn bộ 6 chiến lược đã thử** (0.7204) | Câu 5 vẫn chỉ liên quan ở hạng 2 (0.6859), chưa lên hạng 1 — xem Mục 4 |
| Vũ Đình Huy | RecursiveChunker(500) (398 chunk) | 8/10 (4/5 câu top-1 trúng đích, câu 5 chỉ liên quan) | Top-1 trúng thẳng chi tiết cụ thể ở câu 1 (hạn 15 ngày), câu 2 (Điều 117/120.4/121), câu 3 (2 phương thức thanh toán) | Câu 4 (danh sách hàng cấm) vẫn miss — top-3 không có chunk liệt kê nhóm hàng cấm |
| Nguyễn Thị Nam Phương | RecursiveChunker(500) (398 chunk) | 8/10 (gần như trùng số liệu với Huy vì cùng loại chunker) | Giống Huy — trúng đích câu 1, 2, 3 | Giống Huy — miss câu 4 |
| Lê Quang Trung | RecursiveChunker(500), code ở `src/` gốc (398 chunk) | 8/10 (gần như trùng số liệu với Huy/Phương) | Giống Huy/Phương — trúng đích câu 1, 2, 3 | Giống Huy/Phương — miss câu 4 |
| Lê Tuấn Minh | SentenceChunker(3 câu/chunk) (378 chunk) | 9/10 (4/5 câu) | Trúng đích câu 4 (top-1 = 0.7045) + câu 2, 3 | Câu 5 (quy trình tranh chấp) vẫn chỉ liên quan chung chung, không ra đúng "4 bước" |

> **Chiến lược tốt nhất tính đến hiện tại: `SectionAwareChunker` (Quang Anh, custom v2)** — 9/10, và là chiến lược duy nhất đạt điểm cao nhất tuyệt đối ở câu 4 trong số tất cả các lần thử của cả nhóm. Đồng điểm với `SentenceChunker` (Tuấn Minh) nhưng nhỉnh hơn ở câu 3 (0.7304 vs không rõ ràng bằng) và câu 4 (0.7204 vs 0.7045).



**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **`SentenceChunker` (Lê Tuấn Minh) và `RecursiveChunker(500)` (Huy/Phương/Trung) đều vượt trội hơn `HeadingChunker` và `FixedSizeChunker` của Quang Anh** ở 3/5 câu đầu — vì cả hai đều tạo ra chunk vừa đủ nhỏ để giữ đúng 1 câu/1 đoạn chứa dữ kiện cụ thể (con số, tên điều luật) mà không bị pha loãng bởi nội dung xung quanh như `HeadingChunker` (chunk quá lớn, gồm cả phần mở đầu ít liên quan) hay bị cắt đứt như `FixedSizeChunker`. Đặc biệt, `SentenceChunker` là chiến lược **duy nhất trong cả nhóm** trả lời đúng câu 4 (danh sách hàng cấm) — vì câu mở đầu mục "2.1. Hàng vi phạm bản quyền..." nằm trọn trong 1 chunk 3-câu, trong khi các chiến lược chunk lớn hơn (`RecursiveChunker(500)`, `HeadingChunker`) lại gộp câu mở đầu này chung với các đoạn lân cận kém liên quan hơn, làm loãng điểm số ngữ nghĩa. Bài học: với văn bản luật có cấu trúc liệt kê, **chunk càng nhỏ và bám sát ranh giới câu càng dễ trúng đích các câu hỏi tra cứu chi tiết** — đánh đổi là dễ mất ngữ cảnh tổng thể hơn (không chunk nào tóm tắt được "tất cả bao nhiêu nhóm").

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có thể yêu cầu trả hàng/hoàn tiền trong trường hợp nào? *(metadata_filter={"customer_role": "buyer"})* | Được yêu cầu khi: không nhận được hàng/thiếu số lượng, hàng giả/hàng nhái, sản phẩm lỗi/hư hại khi vận chuyển, người bán giao sai hàng, hàng khác biệt rõ rệt so với mô tả, hàng hết hạn sử dụng, hoặc hai bên tự thỏa thuận; ngoài ra có "Trả hàng COM" khi hàng còn nguyên vẹn nhưng người mua đổi ý. | `shopee-chinh-sach-tra-hang-hoan-tien` — mục 3 "Điều kiện yêu cầu trả hàng/hoàn tiền" |
| 2 | Người bán cần tuân thủ quy định pháp luật nào khi đăng bán sản phẩm trên Shopee? *(metadata_filter={"customer_role": "seller"})* | Phải tuân thủ Điều 117, Điều 120.4, Điều 121 Luật Thương mại và các văn bản pháp luật liên quan đến trưng bày/giới thiệu hàng hóa, dịch vụ; người bán là pháp nhân có vốn đầu tư nước ngoài cần có Giấy phép kinh doanh phù hợp. | `shopee-quy-dinh-dang-ban-san-pham` — mục B.1 "Nguyên tắc chung" |
| 3 | Shopee (bản 2025) chấp nhận những phương thức thanh toán nào? | COD; Ví điện tử ShopeePay/ApplePay/Google Pay hoặc thẻ Visa/Master/JCB/AMEX; chuyển khoản theo Mã đơn hàng; và SPayLater (trả sau theo kỳ hạn). | `shopee-quy-che-hoat-dong` (2025) — Mục V "Quy trình thanh toán" |
| 4 | Danh sách hàng cấm giao dịch trên Shopee gồm những nhóm sản phẩm nào? | Gồm nhiều nhóm: hàng vi phạm bản quyền, thiết bị/trang phục quân đội-công an, tài liệu ảnh hưởng an ninh quốc gia, dịch vụ bất hợp pháp, súng/vũ khí, ma túy/chất kích thích, thuốc lá, sản phẩm người lớn, thiết bị xâm nhập trái phép, hóa chất nguy hiểm dễ cháy nổ, và các mặt hàng khác bị cấm theo pháp luật Việt Nam. | `shopee-quy-che-hoat-dong` (2025) — Mục IX.2 "Danh sách sản phẩm cấm giao dịch" |
| 5 | Quy trình giải quyết tranh chấp giữa người mua và người bán trên Shopee gồm mấy bước? | 4 bước: (1) người mua tạo khiếu nại Trả Hàng/Hoàn Tiền qua ứng dụng/website; (2) bộ phận giải quyết khiếu nại của Shopee tiếp nhận; (3) xử lý trong 7 ngày làm việc kể từ khi nhận đủ thông tin/tài liệu; (4) nếu vượt thẩm quyền, chuyển cơ quan nhà nước có thẩm quyền giải quyết. | `shopee-quy-che-hoat-dong` (2025) — Mục III.6 / phần "Quy trình giải quyết tranh chấp/xử lý khiếu nại" |

> Câu 1 và 2 cần `metadata_filter` theo `customer_role` (buyer/seller) để đáp ứng quy tắc K4_VARIANT. Câu 3 cố ý đối chiếu được với bản 2022 (Mục V bản cũ chỉ có COD + Visa/MasterCard) — dùng để kiểm tra xem retrieval có ưu tiên đúng tài liệu còn hiệu lực hay không (xem Bài 3.5 — Phân tích lỗi).

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Điều kiện trả hàng/hoàn tiền (buyer) | RecursiveChunker(500) / SentenceChunker | Có — top-1 của Huy/Phương/Trung/Tuấn Minh đều trúng thẳng "3.2... trong vòng 15 ngày" | `HeadingChunker` và `FixedSizeChunker` (Quang Anh) chỉ trúng các điều khoản phụ, không có con số 15 ngày ngay ở top-1 |
| 2 | Quy định pháp luật cho người bán (seller) | RecursiveChunker(500) / SentenceChunker | Có (mọi chiến lược) | 4/5 chiến lược có top-1 = đúng đoạn "Điều 117/120.4/121"; chỉ baseline `FixedSizeChunker` của Quang Anh có gold info ở hạng 2-3 |
| 3 | Phương thức thanh toán | Tất cả đều khá tốt | Có (mọi chiến lược) | Các chunk nhỏ (Recursive/Sentence) cho từng phương thức riêng lẻ rất rõ; `HeadingChunker` gộp được nhiều phương thức trong 1 chunk — cả hai cách đều dùng được, tùy mục đích (chi tiết vs. tổng quan) |
| 4 | Danh sách hàng cấm (nhóm sản phẩm) | **SectionAwareChunker (Quang Anh, bản cải tiến)** | **Có** — top-1 trúng thẳng (0.6508); SentenceChunker (Tuấn Minh) cũng trúng | 2 trong 6 lần thử trúng đích rõ ràng; 4 chiến lược ban đầu (Fixed/Heading/Recursive x3) đều miss — xem phân tích ở Mục 4 |
| 5 | Số bước quy trình giải quyết tranh chấp | **Không chiến lược nào ra đúng "4 bước" ở hạng 1** | `SectionAwareChunker` đưa chunk đúng chủ đề vào top-3 (hạng 3) — cải thiện từ miss hẳn thành có liên quan | Vẫn là câu khó nhất của cả nhóm; xem phân tích lỗi ở Mục 4 |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có — câu 1 và câu 2 dùng `metadata_filter={"customer_role": "buyer"/"seller"}` để loại ngay các tài liệu không liên quan vai trò (vd. loại bỏ nhầm lẫn với Mục thanh toán/hàng cấm nằm trong tài liệu Quy chế chung). Nếu không lọc, nguy cơ cao hơn là các chunk từ Quy chế chung (2 phiên bản) sẽ chen vào top-3 vì cùng nói chung chung về "Người Mua/Người Bán", làm loãng kết quả đúng trọng tâm.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Phân tích lỗi (Failure Analysis) — Bài 3.5

**Trường hợp lỗi 1 — Câu 5 "Quy trình giải quyết tranh chấp gồm mấy bước?" (lỗi chính; đã cải thiện một phần, chưa giải quyết triệt để)**
- **Hiện tượng ban đầu:** Top-3 của mọi chiến lược ban đầu (`FixedSizeChunker`, `HeadingChunker`, `RecursiveChunker(500)` x3 người, `SentenceChunker`) đều trả về các đoạn liệt kê **"Bước 1, Bước 2, Bước 3..."** — nhưng lại là các bước của **quy trình thanh toán** hoặc **quy trình mua hàng**, không phải các bước giải quyết tranh chấp/khiếu nại thực sự.
- **Tại sao:** Trong văn bản gốc có tới 3 quy trình khác nhau đều được trình bày theo cùng khuôn mẫu "Bước 1: ... Bước 2: ..." (mua hàng, thanh toán, giải quyết tranh chấp). Về mặt embedding, cấu trúc câu lặp lại này khiến các đoạn có độ tương đồng ngữ nghĩa cao với nhau bất kể chủ đề, nên câu hỏi "quy trình gồm mấy bước" bị hút về quy trình phổ biến/xuất hiện nhiều lần (thanh toán) thay vì đúng đoạn tranh chấp.
- **Đã thử và kết quả:** Quang Anh thiết kế thêm `SectionAwareChunker` — tách theo cả heading La Mã lẫn heading phụ số Ả Rập, luôn giữ dòng tiêu đề (vd. `"III... | 6. Quy trình giải quyết tranh chấp"`) dính vào đầu mỗi chunk con. Chạy thật: chunk đúng chủ đề **lần đầu xuất hiện trong top-3** (hạng 3, score 0.6620) — cải thiện từ "miss hoàn toàn" (0đ) lên "có liên quan trong top-3" (1đ theo rubric `docs/SCORING.md`). Tuy nhiên vẫn chưa lên hạng 1: các đoạn về quy trình mua hàng/thanh toán (xuất hiện nhiều lần hơn trong văn bản, cùng khuôn mẫu câu) vẫn có score cao hơn.
- **Đề xuất cải thiện tiếp theo (chưa thử do giới hạn thời gian):** (1) Diễn đạt câu hỏi cụ thể hơn (thêm từ khoá "khiếu nại" thay vì chỉ "quy trình... bước"); (2) Dùng `search_with_filter` với `category` để loại các chunk thuộc quy trình mua hàng/thanh toán trước khi tìm ngữ nghĩa; (3) Tăng trọng số cho phần tiêu đề trong chunk (vd. lặp lại tiêu đề 2 lần) để tín hiệu chủ đề mạnh hơn so với nội dung các bước.

**Trường hợp lỗi 2 (đã giải quyết) — Câu 4 "Danh sách hàng cấm gồm những nhóm nào?" (2/6 chiến lược ban đầu trúng, cải tiến thứ 3 trúng đích rõ nhất)**
- **Hiện tượng ban đầu:** Với `FixedSizeChunker`, `HeadingChunker` (bản đầu) và `RecursiveChunker(500)` (dùng bởi Huy/Phương/Trung), top-3 không có chunk nào chứa câu mở đầu danh sách hàng cấm — toàn là các điều khoản lân cận (quy định thành viên, bảo vệ người tiêu dùng).
- **2 cách khắc phục, cả hai đều thành công:**
  1. `SentenceChunker(3 câu/chunk)` của Lê Tuấn Minh trúng top-1 (0.7045) — vì chunk nhỏ 3 câu tình cờ gom trọn câu tiêu đề "Danh sách sản phẩm cấm giao dịch..." cùng câu 2.1 đầu tiên.
  2. `SectionAwareChunker` (cải tiến của Quang Anh) trúng top-1 còn rõ hơn (0.6508) — vì **chủ động** giữ tiêu đề Mục "IX. Quản lý thông tin xấu | 2. Danh sách sản phẩm cấm giao dịch..." dính vào mọi chunk con thuộc mục đó, không phụ thuộc may rủi vào ranh giới câu.
- **Tại sao 2 cách đều đúng hướng:** cả hai đều đảm bảo cụm từ tiêu đề "Danh sách sản phẩm cấm giao dịch" nằm trong cùng chunk với nội dung liệt kê, giúp vector embedding mang tín hiệu ngữ nghĩa khớp sát câu hỏi. `SentenceChunker` đạt được điều này một cách tình cờ (do ranh giới 3-câu trùng hợp); `SectionAwareChunker` đạt được một cách **chủ đích** bằng cách gắn cứng tiêu đề Mục — đáng tin cậy hơn vì không phụ thuộc vị trí câu.
- **Bài học:** Khi câu hỏi trùng khớp với một **câu tiêu đề/câu dẫn** ngắn trong tài liệu, gắn tiêu đề Mục vào chunk (chủ động, như `SectionAwareChunker`) đáng tin cậy hơn là hy vọng chunk nhỏ tình cờ giữ được tiêu đề đó (như `SentenceChunker`). Tuy nhiên cả hai vẫn chỉ trả lời được "mục 2.1 là gì", chưa liệt kê đủ cả ~10 nhóm — với câu hỏi **tổng hợp toàn bộ danh sách**, vẫn nên cân nhắc thêm 1 chunk tóm tắt riêng (thủ công hoặc bằng LLM).

### Những phân tích (insights) hay nhất nhóm sẽ trình bày

1. **Chunk càng nhỏ, càng dễ trúng chi tiết cụ thể** (con số, tên điều luật): `RecursiveChunker(500)` và `SentenceChunker(3 câu)` — hai chiến lược có chunk nhỏ hơn — đều vượt trội `HeadingChunker` (chunk lớn) ở câu 1, 2, 3, nơi câu trả lời nằm gọn trong 1-2 câu cụ thể.
2. **Nhưng chunk quá nhỏ không tự động thắng** — nó thắng chỉ khi câu hỏi khớp gần đúng với một câu/cụm từ ngắn trong văn bản (câu 4: `SentenceChunker` trúng nhờ khớp đúng câu tiêu đề danh sách hàng cấm). Với câu hỏi cần tổng hợp nhiều ý rải rác (đếm "mấy bước", liệt kê "tất cả bao nhiêu nhóm"), **không chiến lược chunking nào trong 5 chiến lược đã thử giải quyết trọn vẹn** (câu 5 vẫn miss ở cả 5).
3. Giữ 2 phiên bản Quy chế Shopee (2022 & 2025) trong cùng corpus là con dao hai lưỡi: giúp minh hoạ rất tốt vai trò của `document_version`, nhưng cũng làm loãng kết quả nếu không lọc theo phiên bản mới nhất khi trả lời thật — cả 5 chiến lược đều occasionally trả về chunk từ bản 2022 đã hết hiệu lực.

**Bài học rút ra khi so sánh trong nhóm:**
> So 5 chiến lược thật (đến từ 4 thành viên khác nhau) trên cùng corpus + 5 câu hỏi: `SentenceChunker` (Tuấn Minh) và `RecursiveChunker(500)` (Huy/Phương/Trung) cho kết quả tốt hơn rõ rệt so với `HeadingChunker`/`FixedSizeChunker` (Quang Anh) ở 3/5 câu — vì với các câu hỏi "tra cứu chi tiết" (fact lookup), chunk nhỏ bám sát câu chứa dữ kiện quan trọng hơn là giữ nguyên cả điều khoản. Ngược lại, không chiến lược nào trong nhóm giải quyết được câu hỏi cần **đếm/tổng hợp** (câu 5) — cho thấy giới hạn này không phải do tham số chunking mà do bản chất retrieval theo similarity không có khái niệm "đếm" hay "tóm tắt toàn văn".

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Sẽ thử chunking 2 tầng (parent-child): chunk nhỏ để tìm kiếm chính xác, nhưng khi trả cho agent thì mở rộng lên chunk cha (cả Mục) để giữ ngữ cảnh — đồng thời tách các danh sách liệt kê dài thành chunk riêng có kèm câu tóm tắt ở đầu.

---

## Tự Đánh Giá (Phần Nhóm)

> Đã chạy thật 6 chiến lược (từ 5 thành viên: Quang Anh x3 gồm cả bản cải tiến `SectionAwareChunker`, Huy, Tuấn Minh, Nam Phương, Trung) trên cùng corpus + 5 câu hỏi, dùng code thật của từng người + OpenAI embedder thật. Còn thiếu phần thuyết trình trực tiếp trước lớp.

| Tiêu chí | Điểm tự đánh giá | Vì sao |
|----------|-------------------|--------|
| Lựa chọn tài liệu (Document Set Quality) | **10 / 10** | Rubric chỉ cần 5-10 tài liệu chủ đề rõ + metadata hữu ích + nguồn minh bạch — đã đáp ứng đủ với 5 tài liệu thật (Shopee + Tiki), đủ `source_url`/`retrieved_at`/`document_version`/`customer_role`/`category` |
| Thiết kế chiến lược (Strategy Design) | **15 / 15** | Rubric không bắt buộc chiến lược phải "custom" — chỉ cần giải thích + rationale + so sánh baseline + so sánh thành viên. Đã có đủ cả 4, với 6 lần chạy thật (kể cả 1 vòng lặp cải tiến thật dựa trên phân tích lỗi) |
| Chất lượng truy xuất (Retrieval Quality) | 9 / 10 | Câu 1–4 đạt 2đ (top-3 đúng, có ít nhất 1 chiến lược ở top-1); câu 5 chỉ đạt 1đ vì chunk đúng chủ đề mới lên hạng 3, chưa hạng 1 |
| Thuyết trình (Demo) | 4 / 5 | Nội dung + insight + phân tích lỗi + đề xuất cải tiến đã sẵn sàng; chưa tính điểm demo trực tiếp trước lớp |
| **Tổng phần nhóm** | **38 / 40 (tạm tính)** | |
