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

- `GET /health`: kiểm tra API, model và cache.
- `GET /model/info`: xem version model, update time, feature set, threshold và metric.
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
