# Kế hoạch 3 ngày: Redis + Model v2 + MLflow + Docker

> Mục tiêu tổng: nâng cấp API serving (week_3/API) từ bản demo lên bản gần production.
> Phạm vi: mức **học/demo**, chạy local + docker-compose. Không làm authentication, không deploy cloud.
>
> **Nguyên tắc vàng:** timebox cứng phần cải thiện model. Đích là *dựng pipeline version*, KHÔNG phải đua accuracy.
> Đạt "có v2 chạy song song v1 + đổi nóng được" = PASS, kệ metric.

---

## Quyết định kiến trúc đã chốt

- [ ] Giữ `registry.py` hiện có làm **nơi API serve model** (đã chạy, đã test).
- [ ] MLflow chỉ dùng cho **Tracking** (so sánh v1 vs v2). KHÔNG dùng MLflow Model Registry trong 3 ngày.
- [ ] Mọi lựa chọn backend/version điều khiển qua **biến môi trường** để không phá code cũ.
  - `CACHE_BACKEND=memory|redis`
  - `REDIS_URL=redis://redis:6379/0`
  - `MLFLOW_TRACKING_URI=http://mlflow:5000`

---

## NGÀY 1 — Redis + Docker (hạ tầng, phần "chắc thắng")

### 1A. Redis thay in-memory cache (buổi sáng, ~3h)
- [ ] Thêm `redis` vào `week_3/API/requirements_api.txt`.
- [ ] Tạo interface cache chung (`get / set / clear / stats`) — `TTLMemoryCache` đã có sẵn các method này.
- [ ] Viết class `RedisCache` cùng interface:
  - [ ] Serialize value sang JSON khi set, parse khi get.
  - [ ] Dùng `SETEX` (Redis có TTL gốc → không cần tự quản hết hạn).
  - [ ] Key = ghép tuple thành chuỗi (vd `pred:{model_version}:{dataset}:{visitor}:{visit}:...`).
  - [ ] `stats()` trả `size` qua `DBSIZE` hoặc đếm theo prefix.
- [ ] `CacheManager` chọn backend theo `CACHE_BACKEND` (mặc định `memory` để không phá gì).
- [ ] Cập nhật `config.py`: đọc `REDIS_URL`, `CACHE_BACKEND` từ env.

**Tiêu chí hoàn thành 1A:**
- [ ] `CACHE_BACKEND=memory` → chạy y như cũ.
- [ ] `CACHE_BACKEND=redis` (Redis chạy local) → predict 2 lần, lần 2 `cache_hit=true`.
- [ ] `/cache/status` và `/cache/clear` vẫn hoạt động với Redis.
- [ ] (chốt giá trị) Chạy 2 worker uvicorn + Redis → cache hit dùng chung giữa các worker.

### 1B. Docker hoá (buổi chiều, ~3h)
- [ ] Cài Docker Desktop (cần WSL2 trên Windows) — làm sớm vì hay vướng.
- [ ] Viết `Dockerfile` cho API: base `python:3.13-slim`, cài requirements, chạy `uvicorn`.
- [ ] Viết `.dockerignore` (bỏ `__pycache__`, data nặng, .git...).
- [ ] Viết `docker-compose.yml`: service `api` + `redis`.
  - [ ] API trỏ Redis qua hostname service `redis`.
  - [ ] Mount thư mục `models/` và `data_pyspark_parquet/` vào container qua volume.
- [ ] `docker compose up` → test `/health`, `/predict/session`.

**Tiêu chí hoàn thành 1B:**
- [ ] `docker compose up` lên được cả API + Redis.
- [ ] Gọi API trong container trả kết quả đúng, cache hit qua Redis.

> ⚠️ Bẫy Windows: build lần đầu chậm; mount data parquet cần đúng path; nếu data quá nặng cân nhắc copy 1 phần để test. Để buffer ~1h cho phần này.

---

## NGÀY 2 — MLflow + Model v2 (timebox CHẶT)

### 2A. MLflow Tracking (buổi sáng, ~2h)
- [ ] `pip install mlflow`, thêm vào requirements (file train, không nhất thiết file API).
- [ ] Chạy `mlflow ui` (hoặc thêm service `mlflow` vào compose).
- [ ] Log **model hiện tại làm baseline**: 1 run với params + metrics (lấy từ metadata sẵn có) + artifact model.

**Tiêu chí 2A:**
- [ ] Mở MLflow UI thấy run baseline với đủ metrics (AUC, precision, recall, RMSE...).

### 2B. Model v2 (buổi chiều, TIMEBOX 3h — báo thức!)
- [ ] Thêm 1–3 feature mới HOẶC tinh chỉnh hyperparameter (đã có Optuna trong note.txt).
- [ ] Retrain → log run v2 vào MLflow.
- [ ] Mở UI **so sánh v1 vs v2** trực quan.
- [ ] `registry.register_version(make_active=False, notes="v2: ...")` → **lưu song song bản cũ**, chưa active.
- [ ] Test hot-swap: `POST /model/activate {version: v2}` → predict → rollback `activate {version: v1}`.

**Tiêu chí 2B (đây là PASS của cả mục model):**
- [ ] `GET /model/versions` thấy cả v1 và v2.
- [ ] Activate v2 rồi rollback v1 đều OK, prediction cache tự clear sau mỗi lần đổi.
- [ ] (không bắt buộc) v2 có metric so sánh được với v1 trên MLflow.

> ⏰ Hết 3h mà v2 chưa tốt hơn → vẫn DỪNG, coi như xong. Mục tiêu là pipeline version, không phải accuracy.

---

## NGÀY 3 — Ghép nối + hoàn thiện + buffer

### 3A. Tích hợp toàn bộ (buổi sáng)
- [ ] Chạy `docker-compose` đủ 3 service: `api + redis + mlflow`.
- [ ] (Tùy chọn) A/B hoặc canary đơn giản: % request dùng v2. Nếu thiếu thời gian → chỉ cần demo activate/rollback.

### 3B. Test + tài liệu (buổi chiều)
- [ ] Viết vài **pytest** functional (theo Test Plan trong week_3/API/task): health, predict range, 404, cache_hit, activate/rollback.
- [ ] Viết 1 `locustfile.py` nhỏ: load test `/predict/session`, đo p95.
- [ ] (chốt giá trị) So sánh latency: cache memory vs Redis, cache hit vs miss.
- [ ] Cập nhật `week_3/API/README.md`: hướng dẫn chạy bằng docker-compose, biến môi trường, MLflow.
- [ ] Buffer cho lỗi phát sinh.

**Tiêu chí 3:**
- [ ] `docker compose up` cho ra hệ thống hoàn chỉnh chạy được end-to-end.
- [ ] pytest pass; locust chạy ra số liệu p95.

---

## Bảng theo dõi nhanh (tick khi xong)

| # | Hạng mục | Ngày | Trạng thái |
|---|---|---|---|
| 1 | RedisCache + chọn backend qua env | 1 | ☐ |
| 2 | Dockerfile + docker-compose (api+redis) | 1 | ☐ |
| 3 | MLflow tracking + log baseline | 2 | ☐ |
| 4 | Model v2 + register song song + hot-swap | 2 | ☐ |
| 5 | Compose đủ 3 service (api+redis+mlflow) | 3 | ☐ |
| 6 | pytest + locust + README | 3 | ☐ |

---

## Rủi ro & cách giảm

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| "Cải thiện model" ngốn vô hạn thời gian | **Cao** | Timebox 3h cứng; đích là pipeline không phải accuracy |
| Docker trên Windows vướng (WSL2, mount data) | TB | Cài Docker từ Ngày 1 sáng; copy phần data nhỏ để test |
| Làm trùng registry vs MLflow Registry | TB | Đã chốt: registry serve, MLflow chỉ tracking |
| Data parquet quá nặng để mount/build | TB | Dùng volume thay vì copy vào image; subset khi test |

---

## Phạm vi KHÔNG làm trong 3 ngày (ghi rõ để khỏi sa đà)
- Authentication / rate limiting.
- Deploy cloud (chỉ local + docker-compose).
- MLflow Model Registry (registry tự viết đã đủ).
- A/B testing đầy đủ với thống kê (chỉ canary % đơn giản nếu kịp).
- CI/CD pipeline.
