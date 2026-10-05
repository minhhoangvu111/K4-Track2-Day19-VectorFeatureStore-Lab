# Reflection — Lab 19

**Họ và Tên:** Vũ Minh Hoàng  
**Mã Sinh Viên:** 2A202602371  
**Cohort:** A20-K4 (Track 2 — Day 19)  
**Repository URL:** https://github.com/minhhoangvu111/K4-Track2-Day19-VectorFeatureStore-Lab  
**Path đã chạy:** Lite (fastembed + Qdrant in-memory + SQLite Feast + FastAPI)  

---

## Câu hỏi (≤ 200 chữ)

> Trên golden set 50 queries, mode nào thắng ở loại query nào (`exact` / `paraphrase` / `mixed`), và tại sao? Khi nào bạn **không** dùng hybrid (i.e. khi nào pure BM25 hoặc pure vector là lựa chọn đúng)?

**Kết quả thực nghiệm trên 50 golden queries:**
1. **`exact` queries:** BM25 & Hybrid cùng đạt **100%** Precision@10. Từ khóa kỹ thuật trùng khớp hoàn toàn trong corpus giúp BM25 đạt hiệu năng tuyệt đối mà không phụ thuộc embedding.
2. **`paraphrase` queries:** Hybrid đạt **38.0%** (thắng Vector 28.7% & BM25 32.0%). Vector nắm bắt ngữ nghĩa ngữ cảnh (ví dụ: "tự động mở rộng" $\rightarrow$ "cloud"), giúp bù đắp khi không có từ khóa verbatim.
3. **`mixed` queries:** Hybrid thắng áp đảo với **96.0%** (vs BM25 86% & Vector 83.3%). Thuật toán RRF ($k=60$) kết hợp hoàn hảo độ chính xác keyword và độ phủ semantic.

**Khi nào KHÔNG dùng hybrid:**
- **Pure BM25:** Tra cứu mã SKU, part number, log ID, tên riêng chính xác (cần latency cực thấp < 1ms và không bị vector hallucination/nhiễu).
- **Pure Vector:** Tìm kiếm dữ liệu đa phương tiện (hình ảnh, âm thanh) hoặc query dạng câu hỏi tự do 100% không chứa từ khóa chuyên ngành.
- **Giới hạn hạ tầng:** Khi hệ thống hạn chế tài nguyên compute/RAM và không thể duy trì 2 chỉ mục song song.

---

## Điều ngạc nhiên nhất khi làm lab này

Sự đơn giản nhưng vô cùng hiệu quả của thuật toán RRF ($k=60$). Chỉ với phép cộng nghịch đảo thứ hạng $1/(k + rank)$, Hybrid Search đã cải thiện đáng kể Precision@10 mà không cần huấn luyện mô hình reranker phức tạp.

---

## Bonus challenge

- [ ] Đã làm bonus (xem `bonus/`)
- [ ] Pair work với: _N/A_
