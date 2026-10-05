content = """# Ke Hoach Hoan Thanh Lab Day 19

## Tong quan

Lab: AICB-P2T2 Ngay 19 - Vector Store + Feature Store
Tong diem: 100 pts core (NB1-NB4) + 50 pts nang cao (NB5-NB8) + 20 pts bonus
Path chon: LITE (fastembed + Qdrant in-memory + SQLite Feast + FastAPI) - khong can Docker

## Luong thuc hien

Phase 0 --> Phase 1 --> Phase 2 --> Phase 3 --> Phase 4 --> Phase 5 --> Phase 6
Setup       NB1        NB2         NB3          NB4        NB5-NB8    Submission
~10m        ~20m       ~20m        ~15m         ~25m        ~60m       ~15m

---

## Phase 0 - Setup Moi Truong (Bat buoc)

Muc tieu: Co moi truong chay duoc, tat ca smoke test xanh.

### Cong viec:
- [ ] Copy .env.example -> .env
  - Kiem tra: QDRANT_MODE=memory
  - Kiem tra: EMBEDDING_BACKEND=fastembed
- [ ] Chay: bash setup-lite.sh
  - Tu dong tao virtualenv Python 3.10+
  - Cai tat ca dependencies tu requirements.txt
  - Chay make seed: sinh data/corpus_vn.jsonl (1000 docs VN, 10 topics x 100 docs)
  - Sinh data/golden_set.jsonl (50 golden queries co label)
  - Chay scripts/verify_lite.py (smoke test)
- [ ] Khoi dong Jupyter Lab: make lab
  - Truy cap: http://localhost:8888
  - Mo file 01_embeddings_index.ipynb de bat dau

### Dieu kien PASS Phase 0:
- setup-lite.sh in ra: All checks passed
- data/corpus_vn.jsonl ton tai, co 1000 dong
- data/golden_set.jsonl ton tai, co 50 dong
- Jupyter Lab load duoc tai http://localhost:8888

### Troubleshooting thuong gap:
Loi: python3: command not found
  -> Fix: Cai Python 3.10+ tai https://www.python.org/downloads/

Loi: NB1 bao expected 1000 indexed, got X
  -> Fix: Chay make seed truoc

Loi: feast apply loi
  -> Fix: Xoa app/feast_repo/registry.db roi chay lai

---

## Phase 1 - NB1: Embeddings & Vector Indexing (20 pts)

File: notebooks/01_embeddings_index.py (-> .ipynb)
Diem: 20 pts
Thoi gian: ~20 phut (lan dau cham do download ONNX model ~30-60s)

### Muc tieu:
Hieu qua trinh: text -> vector embedding -> index Qdrant -> similarity search

### Buoc thuc hien:

[S1] Load corpus
  - Doc data/corpus_vn.jsonl -> list 1000 docs
  - Moi doc co: doc_id, topic, title, text
  - In so luong + preview doc dau tien

[S2] Khoi tao embedding model
  - TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
  - Fastembed chay ONNX tren CPU, khong can GPU
  - Kiem tra: vector dim = 384

[S3] Tao Qdrant collection (in-memory)
  - QdrantClient(":memory:") - khong can Docker, chay trong process
  - create_collection("lab19", VectorParams(size=384, distance=Distance.COSINE))
  - Cung API nhu Qdrant production server

[S4] Embed + Upsert toan bo corpus  <-- PHAN CAN IMPLEMENT (TODO)
  - Vong lap batch BATCH=64 docs/lan (CPU-bound, 64 la sweet spot)
  - Moi batch: texts = [d["title"] + " " + d["text"] for d in batch]
  - Embed: vectors = list(embedder.embed(texts))
  - Tao PointStruct(id=..., vector=v.tolist(), payload={doc_id, topic, title})
  - client.upsert(collection_name="lab19", points=points)
  - Xac nhan: client.count("lab19").count == 1000

[S5] Keyword query (similarity search)
  - Query: "cloud computing va tu dong mo rong"
  - Embed query -> query vector
  - client.query_points("lab19", query=q_vec, limit=5)
  - In top-5 ket qua voi score va topic

[S6] Paraphrase query test
  - Query: "phuong phap tu dong mo rong ha tang theo luu luong nguoi dung"
  - KHONG co chu "cloud" trong query!
  - Top-5 phai dominated boi topic "cloud" -> chung minh semantic search hieu y nghia
  - Day la deliverable chinh: chung minh vector search hon keyword match

### Dieu kien PASS (20 pts):
| Tieu chi                                          | Diem  |
| client.count("lab19").count == 1000               | 5 pts |
| Top-5 hien thi cho keyword query (cell S5)        | 5 pts |
| Paraphrase query tra top-5 dung topic cloud       | 10 pts|

### Screenshots can chup va luu vao submission/screenshots/:
1. Cell S4: dong "Indexed: 1000 vectors"
2. Cell S5: top-5 results voi scores
3. Cell S6: paraphrase query -> ket qua cloud cluster

---

## Phase 2 - NB2: Hybrid Search BM25 + Vector + RRF (25 pts)

File: notebooks/02_hybrid_search_rrf.py (-> .ipynb)
Diem: 25 pts
Thoi gian: ~20 phut

### Muc tieu:
Implement Reciprocal Rank Fusion, danh gia Precision@10, chung minh hybrid > keyword va semantic.

### Buoc thuc hien:

[S1] Rebuild ca 2 indices (NB2 standalone)
  - BM25: tokenized = [(d["title"]+" "+d["text"]).lower().split() for d in docs]
         bm25 = BM25Okapi(tokenized)
  - Vector: rebuild Qdrant collection y chang NB1

[S2] Cac ham search don le
  - search_keyword(query, top_k=10):
    scores = bm25.get_scores(query.lower().split())
    ranked = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
    return [docs[i]["doc_id"] for i in ranked]
  
  - search_semantic(query, top_k=10):
    q_vec = next(embedder.embed([query])).tolist()
    res = client.query_points("lab19", query=q_vec, limit=top_k)
    return [p.payload["doc_id"] for p in res.points]

[S3] IMPLEMENT RRF Fusion  <-- QUAN TRONG NHAT, CAN HIEU ROI IMPLEMENT

Cong thuc RRF (deck S3):
  score(d) = SUM over retrievers: 1 / (k + rank_r(d))
  rank_r(d) = vi tri 1-BASED (vi tri dau = 1, KHONG phai 0)
  k = 60 (default cong nghiep)

Implementation:
  def search_hybrid(query, top_k=10, rrf_k=60):
    depth = max(top_k * 5, 50)   # lay 50 ket qua sau tu moi retriever
    kw_ids = search_keyword(query, depth)
    sem_ids = search_semantic(query, depth)
    
    rrf = {}
    # Cong RRF score tu keyword retriever
    for rank, doc_id in enumerate(kw_ids, start=1):  # rank BAT DAU TU 1!
        rrf[doc_id] = rrf.get(doc_id, 0.0) + 1.0 / (rrf_k + rank)
    # Cong RRF score tu semantic retriever
    for rank, doc_id in enumerate(sem_ids, start=1):
        rrf[doc_id] = rrf.get(doc_id, 0.0) + 1.0 / (rrf_k + rank)
    
    # Sort theo tong score, lay top_k
    return [doc_id for doc_id, _ in sorted(rrf.items(), key=lambda kv: -kv[1])[:top_k]]

!! BUG THUONG GAP: rank phai bat dau tu 1, KHONG phai 0 !!
!! Neu dung 0-based: formula sai, hybrid se kem hon du co code dung !!

[S4] Danh gia Precision@10 tren 50 golden queries
  - Doc data/golden_set.jsonl -> 50 queries co label topic
  - P@10 = (so doc trong top-10 thuoc dung topic) / 10
  - Tinh p_kw, p_sem, p_hyb cho moi query
  - In bang: mean(p_kw), mean(p_sem), mean(p_hyb)
  - HYBRID PHAI THANG CA HAI MODE KHAC

[S5] Slice theo loai query
  - Golden set chia 3 loai:
    "exact"      - co tu khoa verbatim trong corpus -> BM25 uu the
    "paraphrase" - dung tu VN khac nghia           -> Vector uu the
    "mixed"      - co ca tu exact + y tuong para   -> HYBRID THANG RO
  - In bang slice: exact/paraphrase/mixed x kw/sem/hyb
  - Key insight: hybrid thang nho robust tren moi kieu query

### Dieu kien PASS (25 pts):
| Tieu chi                                                    | Diem  |
| search_hybrid dung RRF 1/(k+rank), rank 1-based             | 10 pts|
| Avg P@10: hybrid > keyword VA hybrid > semantic             | 10 pts|
| Slice table: hybrid wins mixed, vector wins paraphrase      | 5 pts |

### Screenshots can chup:
1. Cell S4: bang Precision@10 voi hybrid > kw va sem
2. Cell S5: bang slice theo query type (exact/paraphrase/mixed)

---

## Phase 3 - NB3: FastAPI Search Endpoint + Latency Benchmark (25 pts)

File: notebooks/03_search_api_benchmark.py (-> .ipynb)
Diem: 25 pts
Thoi gian: ~15 phut

### Muc tieu:
Boc Searcher thanh REST API, do P50/P95/P99 latency, dam bao hybrid P99 < 50ms.

### Buoc thuc hien:

[S1] Khoi dong API server trong background
  - Popen: uvicorn app.main:app --port 8000 --log-level warning
  - Poll /healthz moi 1s cho den khi {"ready": true}
  - Hoac chay "make api &" trong terminal rieng truoc

[S2] Test single query - kiem tra response shape
  - GET /search?q=cloud+computing+tu+dong+mo+rong&mode=hybrid
  - Response phai co: latency_ms, hits (list), moi hit co doc_id, score, title
  - In top-3 hits + latency

[S3] Latency benchmark (100 queries x 3 modes)
  - Su dung 50 golden queries x 2 reps = 100 calls moi mode
  - Do server-side latency: body["latency_ms"] (da tru network overhead)
  - Do wall-clock: time.perf_counter() quanh httpx call
  - Tinh percentiles: P50, P95, P99
  - In bang:
    mode       P50    P95    P99    P99(wall)
    keyword    ...    ...    ...    ...
    semantic   ...    ...    ...    ...
    hybrid     ...    ...    ...    ...

[S4] Rubric assertion
  - hybrid_p99 = results["hybrid"]["p99_server"]
  - Neu < 50ms: in "PASS - hybrid P99 < 50ms"
  - Neu >= 50ms: chay 10 warm-up queries truoc roi do lai
  - Cold start thuong cham; warm cache se duoi 50ms

[S5] Cleanup
  - proc.terminate() + proc.wait(timeout=5)
  - Dam bao server duoc dong sau khi notebook chay xong

### Dieu kien PASS (25 pts):
| Tieu chi                                           | Diem  |
| /search tra SearchResponse voi latency_ms field    | 5 pts |
| Bang P50/P95/P99 cho 3 modes in ra                 | 10 pts|
| Hybrid P99 server-side < 50ms sau warm-up          | 10 pts|

### Screenshots can chup:
1. Cell S2: 1 response sample voi top-3 hits
2. Cell S3: bang latency P50/P95/P99

---

## Phase 4 - NB4: Feast Feature Store (25 pts)

File: notebooks/04_feast_feature_store.py (-> .ipynb)
Diem: 25 pts
Thoi gian: ~25 phut

### Muc tieu:
Dinh nghia 3 feature views, materialize offline -> online, online lookup P99 < 10ms, PIT join.

### Hieu cau truc Feast:
app/feast_repo/
  feature_store.yaml:
    project: lab19
    provider: local
    online_store: {type: sqlite, path: "data/online_store.db"}
    offline_store: {type: file}
    registry: "data/registry.db"

  feature_views.py:
    user_profile_features:
      entity: user_id
      TTL: 30 ngay (stable profile - thay doi it)
      features: reading_speed_wpm, preferred_language, topic_affinity

    item_popularity_features:
      entity: doc_id
      TTL: 24 gio (popularity thay doi theo ngay)
      features: click_count_24h, ctr_7d, avg_dwell_seconds

    query_velocity_features:
      entity: user_id
      TTL: 1 gio (signal real-time - phai fresh)
      features: queries_last_hour, distinct_topics_24h

### Buoc thuc hien:

[S1] Sinh offline data (Parquet)
  - make_user_profile(n_users=100) -> user_profile.parquet (100 users)
  - make_item_popularity(n_items=1000) -> item_popularity.parquet (1000 items)
  - make_query_velocity(n_users=100) -> query_velocity.parquet (100 users)
  - Save vao app/feast_repo/data/
  - In ten file + kich thuoc

[S2] feast apply - dang ky feature views
  - subprocess.run(["feast", "apply"], cwd=FEAST_DIR, capture_output=True)
  - STDOUT phai co: Created feature view user_profile_features
                    Created feature view item_popularity_features
                    Created feature view query_velocity_features
  - returncode phai == 0
  - Neu loi: xoa app/feast_repo/registry.db roi chay lai

[S3] feast materialize-incremental - load offline -> online
  - end_dt = now.strftime("%Y-%m-%dT%H:%M:%S")
  - subprocess.run(["feast", "materialize-incremental", end_dt], cwd=FEAST_DIR)
  - Log se hien thi so rows da duoc materialize vao SQLite online store
  - returncode phai == 0

[S4] Online lookup - do single latency
  - fs = FeatureStore(repo_path=FEAST_DIR)
  - REQUEST_FEATURES = [
      "user_profile_features:reading_speed_wpm",
      "user_profile_features:preferred_language",
      "user_profile_features:topic_affinity",
      "query_velocity_features:queries_last_hour",
      "query_velocity_features:distinct_topics_24h",
    ]
  - t0 = time.perf_counter()
  - features = fs.get_online_features(features=REQUEST_FEATURES,
      entity_rows=[{"user_id": "u_001"}]).to_dict()
  - In ket qua dict + latency ms

[S5] Batch latency benchmark (100 lookups, P99)  <-- CAN IMPLEMENT
  - Loop 100 lan: lookup user u_000 den u_099
  - Ghi nhan latency moi lan
  - Sort latencies, tinh P50=latencies[50], P95=latencies[95], P99=latencies[99]
  - In: P50, P95, P99
  - Neu P99 < 10ms: in "PASS - online lookup P99 < 10ms"

[S6] PIT join (Point-in-Time join) - offline historical features
  - Tao entity_df:
    user_id  | event_timestamp
    u_001    | now - 2h
    u_002    | now - 1h
    u_003    | now
  - historical = fs.get_historical_features(entity_df=entity_df, features=[...]).to_df()
  - In DataFrame: 3 rows x N features
  - Chung minh: moi user lay feature tai dung thoi diem cua ho (khong co data leakage)

### Dieu kien PASS (25 pts):
| Tieu chi                                              | Diem  |
| feast apply -> 3 feature views registered             | 5 pts |
| materialize-incremental thanh cong, log rows          | 5 pts |
| get_online_features dict hop le cho u_001             | 5 pts |
| 100-call P99 reported (P99 < 10ms = full credit)      | 5 pts |
| PIT join tra 3 rows x N features DataFrame            | 5 pts |

### Screenshots can chup:
1. feast apply STDOUT (hien 3 feature views)
2. materialize log
3. online lookup result + P99 PASS
4. PIT join DataFrame (3 rows)

---

## Phase 5 - NB5-NB8: Advanced Notebooks (50 pts, Optional)

Luu y quan trong: NB5-NB8 dung lai index da dung o NB1 - khong phai embed lai corpus.
Chay truoc: make gen-advanced (de generate data cho NB6, NB8)

### NB5 - Filtered Search (10 pts)
File: notebooks/05_filtered_search.py
- [ ] So sanh 3 chien luoc loc:
      post-filter: search truoc, filter sau -> sap khi filter chat (selectivity ~4%)
      pre-filter:  filter truoc, search trong tap con
      filtered-ANN: Qdrant native filtered search -> giu recall 1.00
- [ ] Bao cao: bang recall theo do chon loc (0%, 10%, 50%, 90%)
- [ ] Over-fetch ladder: fetch_k phai >= 50% corpus moi cuu duoc recall

### NB6 - Agentic Retrieval (12 pts)
File: notebooks/06_agent_retrieval.py
- [ ] Planner tach cau hoi phuc tap -> multiple sub-queries
- [ ] 3 chien luoc cung ngan sach 16 docs: single-shot vs agentic vs agentic+filter
- [ ] Bang so sanh: agentic > single-shot ca recall lan balance
- [ ] Giai thich: tai sao agentic(+filter) thap hon agentic(no filter)
- [ ] build_context(): ket hop Feast features + doc_ids tu retrieval

### NB7 - Semantic Cache (12 pts)
File: notebooks/07_semantic_cache.py
- [ ] Sweep nguong tuong dong: 0.70, 0.75, 0.80, 0.85, 0.90
- [ ] Moi nguong: tinh ca tiet kiem (cache hit rate) VA tra loi sai (error rate)
- [ ] Bieu bang co CA HAI COT (khong chi tiet kiem)
- [ ] Chon nguong hop ly + giai thich tai sao 0.75 chua du
- [ ] Demo ro cheo tenant: leak khi namespaced=False, MISS khi namespaced=True

### NB8 - Feature Engineering (16 pts)
File: notebooks/08_feature_engineering.py
- [ ] Bang leakage: target-naive encoding gap > 0.30 tren session_id, in-fold ≈ 0
- [ ] PIT vs latest join: bao cao % dong bi ro + chenh lech AUC
- [ ] On-demand feature view (ODFV): cung 1 user, 2 gia tri amount khac -> 2 gia tri amount_vs_avg khac

---

## Phase 6 - Kiem tra & Submission

Thoi gian: ~15 phut

### Checklist cuoi:

**Chay lai toan bo de dam bao reproducible:**
- [ ] make test -> 34 tests xanh
- [ ] make verify-lite -> smoke test xanh
- [ ] make benchmark -> in Precision@10 + P99 latency table

**Notebooks phai co output:**
- [ ] NB1 da chay, output cells duoc giu trong .ipynb
- [ ] NB2 da chay, output cells duoc giu
- [ ] NB3 da chay, output cells duoc giu
- [ ] NB4 da chay, output cells duoc giu
- [ ] (Optional) NB5-NB8 da chay

**Screenshots luu vao submission/screenshots/:**
- [ ] nb1_indexed.png: dong "Indexed: 1000 vectors"
- [ ] nb1_paraphrase.png: paraphrase query -> cloud cluster
- [ ] nb2_precision_table.png: bang Precision@10
- [ ] nb3_latency_table.png: bang latency P50/P95/P99
- [ ] nb4_feast_apply.png: feast apply STDOUT
- [ ] nb4_pit_join.png: PIT join DataFrame

**Viet REFLECTION.md:**
- [ ] Mo file submission/REFLECTION.md
- [ ] Viet toi da 200 chu (tieng Viet hoac Anh)
- [ ] Tra loi: mode nao thang loai query nao? Khi nao KHONG dung hybrid?
- [ ] Vi du suy nghi: "BM25 thang exact queries, vector thang paraphrase.
      Hybrid robust hon nhung chi phi tinh toan gap doi. Khong dung hybrid
      khi latency < 10ms la hard constraint, hoac corpus chu yeu la keyword-based."

**Git & GitHub:**
- [ ] git add -A
- [ ] git commit -m "Lab 19 submission - Ho Ten"
- [ ] git push -u origin main
- [ ] Vao GitHub -> Settings -> set repo to PUBLIC
- [ ] Paste URL dang: https://github.com/username/K4-Track2-Day19-VectorFeatureStore-Lab
  vao VinUni LMS Day-19 submission box

Luu y: Repo phai PUBLIC den khi diem duoc cong bo. Private = 0 diem.

---

## Phase 7 - Bonus Challenge (20 pts, Optional)

Xem BONUS-CHALLENGE.md de biet chi tiet.
De tai: Build AI assistant voi hybrid memory ket hop Vector Store + Feature Store.

### Deliverables:
- [ ] bonus/ARCHITECTURE.md
      >= 600 tu
      Co architecture diagram
      3 architecture decisions voi explicit tradeoffs (X vs Y, tai sao chon X)
      1 decision the hien Vietnamese-context awareness
      Named rejected alternative voi ly do
- [ ] bonus/agent.py
      Class HybridMemoryAgent
      Method .remember(text, metadata) -> luu vao vector store
      Method .recall(query, user_id) -> ket hop vector search + Feast features
      Chay duoc khong loi
- [ ] bonus/demo.py
      Exit code 0
      In ra 5 query outputs

---

## Tom tat Diem theo Phase

| Phase   | Noi dung                  | Diem       | Bat buoc? |
|---------|--------------------------|------------|-----------|
| Phase 0 | Setup moi truong         | 0 (prereq) | Co        |
| Phase 1 | NB1 Embeddings           | 20 pts     | Co        |
| Phase 2 | NB2 Hybrid Search RRF    | 25 pts     | Co        |
| Phase 3 | NB3 FastAPI Latency      | 25 pts     | Co        |
| Phase 4 | NB4 Feast Feature Store  | 25 pts     | Co        |
| Phase 5 | NB5-NB8 Advanced         | 50 pts     | Optional  |
| Phase 6 | Reproducible + Submit    | 5 pts      | Co        |
| Phase 7 | Bonus Challenge          | 20 pts     | Optional  |
| TONG    |                          | 175 pts    |           |

Core (bat buoc): 100 pts
Advanced (optional): 50 pts
Bonus (optional):   20 pts
Reproduciblity:      5 pts

---

## Thu tu uu tien neu thoi gian han che

Neu co it thoi gian, lam theo thu tu nay de toi da hoa diem:

Phase 0 -> Phase 1 -> Phase 4 -> Phase 2 -> Phase 3 -> Phase 6
  Setup       NB1       NB4        NB2        NB3       Submit

Ly do:
- Phase 1 (NB1): Nhanh, don gian, phan S4 chi can 1 vong lap
- Phase 4 (NB4): Nhieu buoc nhat, can setup Feast truoc khi co deadline
- Phase 2 (NB2): Core logic la RRF, phai hieu cong thuc
- Phase 3 (NB3): Phu thuoc app.main.py da co san, chu yeu do latency

---

## Ghi chu Vibe-Coding

DELEGATE CHO AI (boilerplate):
- Vong lap upsert batch trong NB1
- Feast feature view Python definitions
- Latency table formatting, statistics
- FastAPI scaffolding (route, Pydantic models)

TU QUYET DINH (judgment decisions):
- Embedding model: bge-small-en (nhanh) vs bge-m3 (tot hon cho tieng Viet, nang hon 4x)
- RRF formula: rank PHAI tu 1, KHONG phai 0 (kiem tra truoc khi chay)
- TTL trong feature views:
    user_profile: 30 ngay (stable) vs query_velocity: 1 gio (real-time signal)
    Neu nham TTL -> fraud detection bo qua tin hieu real-time
- Metric de do: server-side vs wall-clock, P50 vs P99 (rubric check P99)

Moi notebook co vibe-coding callout o cuoi: neu ro phan nao AI lo, phan nao tu nghi.
"""

with open('mydoc/kehoach.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Da ghi xong file mydoc/kehoach.md")
print(f"Kich thuoc: {len(content)} ky tu")
