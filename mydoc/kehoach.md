# Kế Hoạch Hoàn Thành Lab Day 19 — Vector Store + Feature Store

> **Lab:** AICB-P2T2 · Ngày 19 · Vector Store + Feature Store  
> **Sinh viên:** Vũ Minh Hoàng (MSV: 2A202602371)  
> **Repository:** https://github.com/minhhoangvu111/K4-Track2-Day19-VectorFeatureStore-Lab  
> **Path chọn:** ✅ **Lite** (fastembed + Qdrant in-memory + SQLite Feast + FastAPI) — không cần Docker, RAM ~700 MB  

---

## Tổng quan tiến trình

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 (Bonus)
 Setup     NB1       NB2       NB3       NB4      NB5-NB8   Submission
 ~10m      ~20m      ~20m      ~15m      ~25m      ~60m       ~15m
```

---

## Phase 0 — Cài đặt & Khởi động môi trường

**Mục tiêu:** Có môi trường chạy được, tất cả smoke test xanh.

### Công việc:
- [ ] Copy .env.example → .env, kiểm tra: QDRANT_MODE=memory, EMBEDDING_BACKEND=fastembed
- [ ] Chạy: ash setup-lite.sh
  - Tạo virtualenv Python 3.10+
  - Cài deps từ equirements.txt
  - Chạy make seed → sinh data/corpus_vn.jsonl (1000 docs) + data/golden_set.jsonl (50 queries)
  - Chạy smoke test scripts/verify_lite.py
- [ ] Khởi động Jupyter Lab: make lab → mở http://localhost:8888

### Điều kiện pass Phase 0:
- setup-lite.sh in ra: All checks passed
- File data/corpus_vn.jsonl có 1000 dòng
- File data/golden_set.jsonl có 50 dòng
- Jupyter Lab mở được tại http://localhost:8888

### Troubleshooting:
| Lỗi | Cách xử lý |
|-----|-----------|
| python3: command not found | Cài Python 3.10+ tại python.org |
| NB1 báo expected 1000 indexed, got X | Chạy make seed |
| Port 8888 bị chiếm | Kill process đang chiếm port |

---

## Phase 1 — NB1: Embeddings & Vector Indexing

**File:** 
otebooks/01_embeddings_index.py  
**Điểm rubric:** 20 pts  
**Thời gian:** ~20 phút (lần đầu chậm do download ONNX model)

### Mục tiêu:
Hiểu text → vector (embedding), index vào Qdrant, similarity search.

### Công việc:

**S1: Load corpus**
- [ ] Đọc data/corpus_vn.jsonl → 1000 docs (doc_id, topic, title, text)

**S2: Khởi tạo embedding model**
- [ ] TextEmbedding(model_name="BAAI/bge-small-en-v1.5") — 384-dim

**S3: Tạo Qdrant collection (in-memory)**
- [ ] QdrantClient(":memory:") — không cần Docker
- [ ] create_collection("lab19", VectorParams(size=384, distance=Distance.COSINE))

**S4: Embed + Upsert corpus (TODO)**
- [ ] Vòng lặp batch 64 docs/lần: embed title + text → PointStruct → upsert
- [ ] Xác nhận: client.count("lab19").count == 1000

**S5: Keyword query**
- [ ] Query: "cloud computing và tự động mở rộng" → top-5 + scores

**S6: Paraphrase query test**
- [ ] Query: "phương pháp tự động mở rộng hạ tầng theo lưu lượng người dùng" (không có chữ "cloud")
- [ ] Top-5 phải dominated bởi topic cloud

### Điều kiện pass (20 pts):
| Tiêu chí | Điểm |
|---------|------|
| count == 1000 | 5 pts |
| Top-5 keyword query hiển thị | 5 pts |
| Paraphrase query đúng topic cloud | 10 pts |

### Screenshots cần chụp:
1. Cell S4: Indexed: 1000 vectors
2. Cell S5: top-5 results với scores
3. Cell S6: paraphrase → cloud cluster

---

## Phase 2 — NB2: Hybrid Search BM25 + Vector + RRF

**File:** 
otebooks/02_hybrid_search_rrf.py  
**Điểm rubric:** 25 pts  
**Thời gian:** ~20 phút

### Mục tiêu:
Implement RRF fusion, đo Precision@10, chứng minh hybrid > keyword và semantic.

### Công việc:

**S1: Rebuild cả 2 indices**
- [ ] BM25: BM25Okapi(tokenized) — tokenize .lower().split()
- [ ] Vector: rebuild Qdrant collection

**S2: Search functions**
- [ ] search_keyword(query, top_k=10) — BM25 → doc_ids
- [ ] search_semantic(query, top_k=10) — embed → Qdrant → doc_ids

**S3: RRF Fusion (TODO — QUAN TRỌNG NHẤT)**
`python
def search_hybrid(query, top_k=10, rrf_k=60):
    depth = max(top_k * 5, 50)
    kw_ids = search_keyword(query, depth)
    sem_ids = search_semantic(query, depth)
    rrf = {}
    for rank, doc_id in enumerate(kw_ids, start=1):   # rank từ 1!
        rrf[doc_id] = rrf.get(doc_id, 0) + 1.0 / (rrf_k + rank)
    for rank, doc_id in enumerate(sem_ids, start=1):
        rrf[doc_id] = rrf.get(doc_id, 0) + 1.0 / (rrf_k + rank)
    return [d for d, _ in sorted(rrf.items(), key=lambda x: -x[1])[:top_k]]
`
> BUG THƯỜNG GẶP: rank phải từ **1**, KHÔNG phải 0!

**S4: Đánh giá P@10 trên 50 golden queries**
- [ ] Tính P@10 = fraction top-10 đúng topic
- [ ] In bảng: keyword / semantic / hybrid — hybrid phải thắng

**S5: Slice theo loại query**
- [ ] exact → BM25 mạnh
- [ ] paraphrase → semantic mạnh
- [ ] mixed → **hybrid thắng rõ nhất**

### Điều kiện pass (25 pts):
| Tiêu chí | Điểm |
|---------|------|
| RRF đúng formula 1/(k+rank), rank 1-based | 10 pts |
| Avg P@10: hybrid > keyword VÀ > semantic | 10 pts |
| Slice table đúng pattern | 5 pts |

### Screenshots cần chụp:
1. Cell S4: bảng Precision@10
2. Cell S5: bảng slice theo query type

---

## Phase 3 — NB3: FastAPI + Latency Benchmark

**File:** 
otebooks/03_search_api_benchmark.py  
**Điểm rubric:** 25 pts  
**Thời gian:** ~15 phút

### Mục tiêu:
REST API cho search, đo P50/P95/P99, hybrid P99 < 50ms.

### Công việc:

**S1: Khởi động API server**
- [ ] Popen uvicorn pp.main:app port 8000 trong background
- [ ] Đợi /healthz → {"ready": true}

**S2: Test single query**
- [ ] GET /search?q=cloud+computing&mode=hybrid
- [ ] Verify: có latency_ms field + hits list

**S3: Latency benchmark**
- [ ] 50 golden queries × 2 reps = 100 calls/mode
- [ ] Đo ody["latency_ms"] (server-side)
- [ ] Bảng P50/P95/P99 cho keyword / semantic / hybrid

**S4: Rubric assertion**
- [ ] hybrid P99 server-side < 50ms → PASS
- [ ] Nếu fail: chạy 10 warm-up queries trước

**S5: Cleanup**
- [ ] proc.terminate() sau khi xong

### Điều kiện pass (25 pts):
| Tiêu chí | Điểm |
|---------|------|
| /search trả SearchResponse với latency_ms | 5 pts |
| Bảng P50/P95/P99 cho 3 modes in ra | 10 pts |
| Hybrid P99 < 50ms sau warm-up | 10 pts |

### Screenshots cần chụp:
1. Cell S2: response + top-3 hits
2. Cell S3: bảng latency

---

## Phase 4 — NB4: Feast Feature Store

**File:** 
otebooks/04_feast_feature_store.py  
**Điểm rubric:** 25 pts  
**Thời gian:** ~25 phút

### Mục tiêu:
3 feature views → feast apply → materialize → online lookup < 10ms P99 → PIT join.

### Cấu trúc Feast:
`
app/feast_repo/
├── feature_store.yaml     # config (lite: SQLite online store)
└── feature_views.py       # 3 feature views:
    ├── user_profile_features    (TTL=30 ngày, entity: user_id)
    ├── item_popularity_features (TTL=24 giờ, entity: doc_id)
    └── query_velocity_features  (TTL=1 giờ,  entity: user_id)
`

### Công việc:

**S1: Sinh offline data (Parquet)**
- [ ] make_user_profile(100) → user_profile.parquet
- [ ] make_item_popularity(1000) → item_popularity.parquet
- [ ] make_query_velocity(100) → query_velocity.parquet

**S2: feast apply**
- [ ] subprocess.run(["feast", "apply"], cwd=FEAST_DIR)
- [ ] STDOUT: Created feature view <name> × 3

**S3: feast materialize-incremental**
- [ ] Materialize đến 
ow
- [ ] Log in ra rows materialized

**S4: Online lookup + single latency**
- [ ] s.get_online_features(features=[...], entity_rows=[{"user_id":"u_001"}])
- [ ] In kết quả dict + latency ms

**S5: Batch latency benchmark (100 lookups)**
- [ ] Loop 100 lần, tính P50/P95/P99
- [ ] P99 < 10ms → PASS

**S6: PIT join**
- [ ] 3 users × 3 timestamps → entity_df
- [ ] s.get_historical_features(entity_df, features=[...]) → DataFrame 3×N
- [ ] In DataFrame

> Nếu east apply lỗi: xóa pp/feast_repo/registry.db rồi chạy lại

### Điều kiện pass (25 pts):
| Tiêu chí | Điểm |
|---------|------|
| feast apply → 3 feature views registered | 5 pts |
| materialize-incremental thành công, log rows | 5 pts |
| get_online_features dict hợp lệ cho u_001 | 5 pts |
| 100-call P99 reported (P99 < 10ms = full credit) | 5 pts |
| PIT join 3 rows × N features | 5 pts |

### Screenshots cần chụp:
1. feast apply STDOUT
2. materialize log
3. online lookup result + P99 PASS
4. PIT join DataFrame

---

## Phase 5 — NB5–NB8: Advanced Notebooks

**Điểm:** 50 pts (optional nhưng khuyến khích)  
**Lưu ý:** Chạy make gen-advanced để generate data cho NB6, NB8.

### NB5 — Filtered Search (10 pts)
- [ ] Bảng recall theo selectivity: post-filter sập khi ~4%, filtered-ANN giữ 1.00
- [ ] Over-fetch ladder: fetch_k ≈ 50% corpus

### NB6 — Agentic Retrieval (12 pts)
- [ ] Planner tách câu hỏi → sub-queries
- [ ] Bảng 3 chiến lược cùng ngân sách 16 docs: agentic > single-shot
- [ ] uild_context() = Feast features + doc_ids

### NB7 — Semantic Cache (12 pts)
- [ ] Bảng sweep ngưỡng: cả tiết kiệm VÀ trả lời sai
- [ ] Chọn ngưỡng hợp lý + giải thích
- [ ] Demo rò tenant: leak khi namespaced=False, MISS khi True

### NB8 — Feature Engineering (16 pts)
- [ ] Bảng leakage: target-naive gap > 0.30 trên session_id
- [ ] PIT vs latest join: % dòng rò + AUC diff
- [ ] ODFV: cùng user, 2 amount → 2 amount_vs_avg khác nhau

---

## Phase 6 — Kiểm tra & Submission

**Thời gian:** ~15 phút

### Checklist cuối:

**Chạy lại toàn bộ:**
- [ ] make test → 34 tests xanh
- [ ] make verify-lite → smoke test xanh
- [ ] make benchmark → Precision@10 + P99 table

**Notebooks:**
- [ ] NB1–NB4 đã chạy, output cells được giữ trong .ipynb
- [ ] (Optional) NB5–NB8 đã chạy

**Screenshots (vào submission/screenshots/):**
- [ ] NB1: Indexed 1000 + top-5 paraphrase
- [ ] NB2: bảng Precision@10
- [ ] NB3: API response + bảng latency
- [ ] NB4: feast apply + lookup + PIT join

**REFLECTION.md:**
- [ ] Điền submission/REFLECTION.md (≤ 200 chữ)
- [ ] Trả lời: mode nào thắng loại query nào? Khi nào KHÔNG dùng hybrid?

**Git & GitHub:**
- [ ] git add -A
- [ ] git commit -m "Lab 19 submission — <Họ Tên>"
- [ ] git push -u origin main
- [ ] Set repo PUBLIC trên GitHub
- [ ] Paste URL vào VinUni LMS Day-19

---

## Phase 7 (Optional) — Bonus Challenge

**Điểm:** +20 pts bonus

### Deliverables:
- [ ] onus/ARCHITECTURE.md — ≥ 600 chữ + diagram + 3 decisions với tradeoffs
- [ ] onus/agent.py — HybridMemoryAgent.remember() + .recall()
- [ ] onus/demo.py — exit 0, in 5 query outputs

---

## Tóm tắt điểm

| Phase | Nội dung | Điểm | Bắt buộc? |
|-------|---------|------|----------|
| Phase 0 | Setup môi trường | - | ✅ |
| Phase 1 | NB1 Embeddings | 20 pts | ✅ |
| Phase 2 | NB2 Hybrid RRF | 25 pts | ✅ |
| Phase 3 | NB3 FastAPI Latency | 25 pts | ✅ |
| Phase 4 | NB4 Feast Store | 25 pts | ✅ |
| Phase 5 | NB5–NB8 Advanced | 50 pts | ⭐ Optional |
| Phase 6 | Reproducible + Submission | 5 pts | ✅ |
| Phase 7 | Bonus Challenge | 20 pts | 🎁 Optional |
| **Tổng** | | **175 pts tối đa** | |

---

## Thứ tự ưu tiên nếu thời gian hạn chế

`
Phase 0 → Phase 1 → Phase 4 → Phase 2 → Phase 3 → Phase 6
(setup)    (NB1)    (NB4 nhiều   (NB2)     (NB3)    (submit)
           đơn giản  steps nhất)
`

> **Tip vibe-coding:** Dùng AI để generate boilerplate (upsert loop, Feast definitions,
> latency table). Tự quyết định: embedding model, RRF formula (rank 1-based!),
> TTL feature views, metric cần đo. Đây là judgment decisions — không delegate cho AI.
