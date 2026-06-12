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
- `POST /sessions/lookup`: nhập `visitor_id + session_id`, trả session info, feature và ground truth nếu có.
- `POST /predict/session`: lookup session, chạy model live và trả probability/revenue.
- `GET /cache/status`: xem số item trong feature cache và prediction cache.
- `POST /cache/clear`: xóa cache.

## Ví dụ request

```json
{
  "visitor_id": "1234567890",
  "session_id": 1520000000,
  "dataset": "auto",
  "include_features": true,
  "include_ground_truth": true
}
```

## Cache trong API

API dùng in-memory cache cho V1:

- Model cache: model `.pkl` và metadata JSON được load một lần lúc startup.
- Feature lookup cache: cache theo `(dataset, visitor_id, session_id)`.
- Prediction cache: cache theo `(model_version, dataset, visitor_id, session_id, include_features, include_ground_truth)`.

Khi model version đổi, prediction cache cũ không bị dùng nhầm vì `model_version` là một phần của cache key.
