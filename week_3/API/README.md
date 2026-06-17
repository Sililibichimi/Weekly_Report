# Week 3 API Serving

FastAPI service cho bài toán dự đoán user có mua hàng trong 30 ngày sau session hiện tại hay không, và expected revenue trong 30 ngày đó.

## Chạy API

```powershell
pip install -r week_3\API\requirements_api.txt
uvicorn week_3.API.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Endpoints

- `GET /health`: kiểm tra API, model, version đang active và cache.
- `GET /model/info`: xem version model, update time, feature set, threshold và metric.
- `GET /model/versions`: liệt kê tất cả version model trong registry + version đang active.
- `POST /model/activate`: đổi sang version model khác ngay khi đang chạy (hot-swap, không restart).
- `POST /model/reload`: nạp lại version đang active (dùng khi file model bị thay).
- `POST /sessions/lookup`: nhập `visitor_id + visit_id`, trả session info, feature và ground truth nếu có.
- `POST /predict/session`: lookup session, chạy model live và trả probability/revenue.
- `GET /cache/status`: xem số item trong feature cache và prediction cache.
- `POST /cache/clear`: xóa cache.

## Ví dụ request
- kết quả là không mua:
```json
{
  "visitor_id": "0000268499301061358",
  "visit_id": 1527179361,
  "dataset": "test",
  "include_features": true,
  "include_ground_truth": true
}
```
- Kết quả là có mua:
```json
{
  "visitor_id": "0038323288872790098",
  "visit_id": 1527187973,
  "dataset": "test",
  "include_features": true,
  "include_ground_truth": true
}
```

`POST /predict/session` có thêm block dễ đọc:

```text
visitor_id | session_id | model_version | time_update | Xác suất mua | Doanh thu
```

Trong JSON response, block này nằm ở `result_summary`:

```json
{
  "result_summary": {
    "visitor_id": "0038323288872790098",
    "session_id": 1527187973,
    "model_version": "lgbm_30d_20260611T165819",
    "time_update": "2026-06-11T16:58:19.623984+00:00",
    "xac_suat_mua": 0.87,
    "doanh_thu": 123.45
  }
}
```

API vẫn nhận `visit_id`; nếu muốn gọi theo đúng cách hiểu business, có thể gửi `session_id` thay cho `visit_id`.

## Cache trong API

API dùng in-memory cache cho V1:

- Model cache: model `.pkl` và metadata JSON được load một lần lúc startup.
- Feature lookup cache: cache theo `(dataset, visitor_id, visit_id)`.
- Prediction cache: cache theo `(model_version, dataset, visitor_id, visit_id, include_features, include_ground_truth)`.

Khi model version đổi, prediction cache cũ không bị dùng nhầm vì `model_version` là một phần của cache key.

## Quản lý version model (Model Registry)

API dùng một registry file nhẹ để quản lý nhiều version model.

Cấu trúc trên đĩa:

```text
models/
├── registry.json                 # danh sách version + con trỏ active_version
├── v20260615T092320/             # 1 folder = 1 version
│   ├── lgbm_purchase_classifier_30d.pkl
│   ├── lgbm_revenue_regressor_30d.pkl
│   └── lgbm_modeling_preprocessing_30d.json
└── ...
```

- `registry.json` giữ metadata của từng version (created_at, feature_set, feature_count, threshold, notes) và một `active_version`.
- Lúc startup, API đọc `active_version` từ registry rồi load đúng version đó. Nếu chưa có `registry.json` (lần đầu), API tự **bootstrap** từ các file model phẳng đang có trong `models/` (copy vào folder version, không xóa file cũ).

### Đăng ký version mới sau khi train

Trong code (ví dụ cuối notebook train, sau khi đã lưu 2 `.pkl` + metadata JSON):

```python
from week_3.API.registry import ModelRegistry

registry = ModelRegistry()
version = registry.register_version(
    classifier_src="models/lgbm_purchase_classifier_30d.pkl",
    regressor_src="models/lgbm_revenue_regressor_30d.pkl",
    metadata_src="models/lgbm_modeling_preprocessing_30d.json",
    make_active=False,   # đăng ký trước, chưa cho chạy production ngay
    notes="thêm feature X, retrain tháng 6",
)
print("registered:", version)   # version id suy ra từ created_at_utc trong metadata
```

### Đổi version khi API đang chạy (hot-swap)

```powershell
# Xem các version
curl http://127.0.0.1:8000/model/versions

# Đổi sang version khác (không cần restart)
curl -X POST http://127.0.0.1:8000/model/activate -H "Content-Type: application/json" -d '{"version":"v20260615T092320"}'
```

Khi `activate`:
- API load version mới vào một `ModelService` + `FeatureStore` mới rồi mới **swap** (đổi tham chiếu) dưới khóa → request đang chạy không thấy trạng thái nửa vời.
- Prediction cache được xóa (vì kết quả của model cũ không còn dùng lại được). Feature cache giữ nguyên (không phụ thuộc model).
- Chỉ ghi `active_version` xuống `registry.json` **sau khi** load thành công → nếu version lỗi, registry không bị trỏ vào bản hỏng.

> Lưu ý: cache + active version là per-process. Nếu chạy nhiều worker uvicorn, mỗi worker cần activate riêng (hoặc dùng registry chung + restart). Đây là giới hạn V1 giống phần cache.
