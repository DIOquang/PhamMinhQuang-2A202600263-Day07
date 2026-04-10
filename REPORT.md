# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Minh Quang 2A202600263
**Nhóm:** 68
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Nó cho thấy các vector có độ lệch góc rất nhỏ, nghĩa là chúng cùng hướng trong không gian ngữ nghĩa 768 chiều. Điều này tương ứng với việc văn bản có nội dung rất tương đồng.

**Ví dụ HIGH similarity:**
- Sentence A: "The student is studying for the exam."
- Sentence B: "A learner is preparing for their test."
- Tại sao tương đồng: Sử dụng các từ đồng nghĩa để diễn tả cùng một hành động học tập.

**Ví dụ LOW similarity:**
- Sentence A: "I love coding in Python."
- Sentence B: "The ocean is full of marine life."
- Tại sao khác: Một câu về kỹ thuật, một câu về thiên nhiên.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Vì văn bản thường có độ dài không đồng nhất. Euclidean distance sẽ đo khoảng cách vật lý giữa các điểm, vốn bị ảnh hưởng bởi số lượng từ, trong khi Cosine similarity chỉ đo sự tương đồng về phong cách/nội dung thông qua hướng vector.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** VinUni 20K AI Talent Program Handbook

**Tại sao nhóm chọn domain này?**
Chương trình Đào tạo Nhân tài AI Thực chiến (20K AI) của VinUni là một domain thực tế, có cấu trúc tài liệu rõ ràng và nội dung đa dạng (từ kỹ thuật, lịch trình đến quy định chính sách). Đây là bộ dữ liệu lý tưởng để kiểm thử khả năng trích xuất thông tin và trả lời câu hỏi của hệ thống RAG.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | 01_highlights.md | VinUni AI Handbook | ~1500 | category: overview |
| 2 | 02_structure.md | VinUni AI Handbook | ~1000 | category: academic |
| 3 | 03_internships.md | VinUni AI Handbook | ~800 | category: logistics |
| 4 | 04_schedule.md | VinUni AI Handbook | ~2000 | category: logistics |
| 5 | 05_evaluation.md | VinUni AI Handbook | ~500 | category: academic |
| 6 | 06_lms.md | VinUni AI Handbook | ~800 | category: systems |
| 7 | 07_services.md | VinUni AI Handbook | ~2500 | category: logistics |
| 8 | 08_regulations.md | VinUni AI Handbook | ~2000 | category: policy |
| 9 | 09_completion_stipend.md | VinUni AI Handbook | ~2000 | category: policy |
| 10 | 10_faqs.md | VinUni AI Handbook | ~5000 | category: faq |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | string | academic, policy, logistics | Giúp lọc nhanh các chủ đề cụ thể (ví dụ: chỉ tìm trong chính sách). |
| source | string | 20K AI Handbook v1.0 | Truy xuất nguồn gốc tài liệu để đối chiếu khi cần. |
| language | string | Vietnamese | Lọc ngôn ngữ nếu hệ thống hỗ trợ đa ngữ. |
| last_updated | string | 2025-04 | Đảm bảo thông tin truy xuất là mới nhất. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| 10_faqs.md | FixedSizeChunker (`fixed_size`) | 39 | 197.4 | Low |
| 10_faqs.md | SentenceChunker (`by_sentences`) | 18 | 317.9 | High |
| 10_faqs.md | RecursiveChunker (`recursive`) | 39 | 146.8 | High |

### Strategy Của Tôi

**Loại:** `RecursiveChunker`

**Mô tả cách hoạt động:**
Chiến lược này chia nhỏ văn bản theo nhiều cấp độ phân tách (đoạn văn, dòng, từ). Nó hoạt động đệ quy để đảm bảo các chunk luôn ở dưới mức kích thước quy định (`chunk_size`) mà vẫn cố gắng giữ các khối văn bản liên quan ở cạnh nhau.

**Tại sao tôi chọn strategy này cho domain nhóm?**
Handbook là loại tài liệu hỗn hợp. `RecursiveChunker` linh hoạt hơn các phương pháp khác vì nó có thể xử lý tốt cả những đoạn văn dài và các danh sách liệt kê ngắn mà không làm mất đi tính liên kết của dữ liệu.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| 10_faqs.md | FixedSizeChunker (baseline) | 39 | 197.4 | Medium |
| 10_faqs.md | **RecursiveChunker** | 39 | 146.8 | **High** |

---

## 4. My Approach — Cá nhân (10 điểm)

### Chunking Functions

**SentenceChunker.chunk** — approach:
Tôi sử dụng Regex để tách văn bản thành list các câu, sau đó dùng sliding window để nhóm các câu lại với nhau tùy theo cấu hình `max_sentences`.

**RecursiveChunker.chunk / _split** — approach:
Tôi xây dựng hàm đệ quy với danh sách các dấu phân cách thông minh, ưu tiên giữ lại các cấu trúc lớn như đoạn văn trước khi buộc phải chia nhỏ thành câu hoặc từ.

### EmbeddingStore

**add_documents + search** — approach:
Tôi quản lý metadata rất kỹ khi nạp document. Trong hàm search, tôi tính toán dot product để tìm ra các vector có độ tương đồng cao nhất.

**search_with_filter + delete_document** — approach:
Tôi thực hiện so khớp metadata dictionary để hỗ trợ lọc nâng cao. Với chức năng xóa, tôi đảm bảo cập nhật lại cả ID và metadata để dữ liệu luôn sạch bóng.

### KnowledgeBaseAgent

**answer** — approach:
Tôi tối ưu hóa prompt để LLM có thể đọc hiểu context tốt nhất. Agent sẽ tổng hợp các chunk tìm được thành một đoạn văn duy nhất làm đầu vào cho LLM.

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | The cat sits on the mat. | The cat is sitting on the mat. | high | 0.98 | Đúng |
| 2 | Python is a programming language. | I like to eat apples. | low | 0.07 | Đúng |
| 3 | The weather is beautiful today. | It is a sunny day. | high | 0.71 | Đúng |
| 4 | The stock market is volatile. | Financial markets experience fluctuations. | high | 0.66 | Đúng |
| 5 | A dog is a loyal friend. | Computers process data quickly. | low | -0.05 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Cặp 3 cho thấy sức mạnh của Embedder trong việc hiểu ngữ cảnh thời tiết mặc dù từ vựng khác nhau hoàn toàn.

---

## 6. Results — Cá nhân (10 điểm)

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Quy trình đánh giá học viên trong chương trình 20K AI như thế nào? | Được đánh giá dựa trên: 1. Lab hàng ngày; 2. Dự án #build; 3. Thi giữa kỳ (tuần 6); 4. Thực chiến doanh nghiệp; 5. Chuyên cần. |
| 2 | Học viên nhận được bao nhiêu tiền trợ cấp mỗi tháng và điều kiện nhận là gì? | Nhận 8 triệu VNĐ/tháng. Điều kiện: Tuân thủ cam kết, duy trì chuyên cần, hoàn thành bài tập, tuân thủ kỷ luật/bảo mật. |
| 3 | Có những dịch vụ ăn uống và tiện ích nào tại campus VinUni? | Wifi riêng, thư viện, canteen, Highlands Coffee, Fresh Garden, trạm sạc xe điện miễn phí. |
| 4 | Cấu trúc chương trình đào tạo kéo dài mấy tuần và chia làm mấy giai đoạn? | 12 tuần, 3 giai đoạn: GĐ1 (3 tuần) Nền tảng, GĐ2 (3 tuần) Chuyên sâu, GĐ3 (6 tuần) Thực chiến. |
| 5 | Các quy định về chuyên cần trong giai đoạn học tập tại trường là gì? | Nghỉ tối đa 4 buổi trong GĐ1 & 2. Không nghỉ 2 buổi liên tiếp trong 1 tuần. Cần báo trước lý do chính đáng. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Quy trình đánh giá học viên... | "Khi tham gia chương trình, học viên được..." | 0.81 | No | [MOCK] Nhầm sang phần tài chính. |
| 2 | Học viên nhận được bao nhiêu... | "Điều kiện nhận trợ cấp Học viên được nhận trợ cấp..." | 0.80 | Yes | [MOCK] Đúng về điều kiện nhận trợ cấp. |
| 3 | Có những dịch vụ ăn uống... | "Học viên có thể sử dụng các dịch vụ ăn uống..." | 0.53 | Yes | [MOCK] Tìm được thông tin ăn uống. |
| 4 | Cấu trúc chương trình... | "# Quy định đào tạo  ###### **1. Quy định chuyên cần**..." | 0.80 | No | [MOCK] Nhầm sang phần chuyên cần. |
| 5 | Các quy định về chuyên cần... | "# Đánh giá quá trình học tập Học viên sẽ được đánh giá..." | 0.80 | No | [MOCK] Nhầm sang phần đánh giá. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 2 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Metadata Filter là chìa khóa để giải quyết các truy vấn bị chồng lấn nội dung.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Giao diện demo đẹp giúp người dùng tin tưởng vào kết quả RAG hơn.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ bổ sung thêm tóm tắt (summary) cho mỗi file để làm giàu thông tin metadata.

---

## Tự Đánh Giá (94/100)
