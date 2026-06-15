# Project Documentation - Future 30D Purchase & Revenue Prediction

## 1. Tổng quan bài toán

Bài toán: tại mỗi session hiện tại của một user, dựa trên thông tin session hiện tại và lịch sử trước đó của user, dự đoán:

- User có phát sinh mua hàng trong 30 ngày tiếp theo hay không.
- Nếu có, tổng doanh thu trong 30 ngày tiếp theo là bao nhiêu.

| Thành phần | Mô tả |
|---|---|
| Grain | 1 dòng = 1 user tại 1 session |
| Key | `fullVisitorId` + `visit_id` |
| Input | Current session + lịch sử trước session hiện tại |
| Classification target | `future_30d_has_purchase` |
| Revenue target | `future_30d_revenue` |
| Model output | Purchase probability + expected revenue |

Điểm quan trọng của bài toán là phải xử lý đúng yếu tố thời gian. Khi tạo feature, chỉ được dùng thông tin trước hoặc tại session hiện tại; khi tạo label, mới nhìn vào 30 ngày sau session hiện tại. Nếu không tách rõ hai phần này, model rất dễ bị leakage.

## 2. Công cụ chính: PySpark và Parquet

### 2.1. PySpark

PySpark là công cụ xử lý dữ liệu chính trong pipeline từ notebook `01` đến `05`.

PySpark được dùng cho:

- Đọc raw CSV lớn.
- Parse các cột JSON như `totals`, `device`, `geoNetwork`, `trafficSource`.
- Chuẩn hóa schema, kiểu dữ liệu và các cột session-level.
- Kiểm tra data quality trên toàn bộ dữ liệu.
- Dedupe session bằng window function.
- Tạo label 30 ngày bằng logic theo user timeline.
- Tạo feature lịch sử user bằng window function.
- Ghi output trung gian ra Parquet.

Vì sao chọn PySpark:

- Dataset train có 1,708,337 rows và test có 401,589 rows; nếu dùng Pandas toàn bộ pipeline sẽ dễ tốn RAM khi parse JSON, join theo user và tạo feature lịch sử.
- Spark phù hợp với các thao tác column transformation, aggregation, join và window function.
- Cách làm này gần với flow xử lý dữ liệu trong môi trường production hơn so với chỉ dùng Pandas notebook.

Vấn đề thực sự cần lưu ý:

| Vấn đề | Cách xử lý |
|---|---|
| CSV có nhiều cột JSON dạng string | Parse thành các cột phẳng có prefix rõ ràng |
| Numeric columns ban đầu chưa sạch | Ép kiểu và fill giá trị thiếu theo logic từng cột |
| Join/window theo user có thể nặng | Chỉ giữ cột cần thiết, ghi output trung gian ra Parquet |
| Spark lazy evaluation nên lỗi có thể xuất hiện muộn | Kiểm tra trên sample trước, sau đó mới chạy full data |

### 2.2. Parquet

Parquet được dùng làm format lưu trữ trung gian thay cho việc đọc CSV lại ở mỗi bước.

Vì sao chọn Parquet:

- Parquet là columnar format, đọc nhanh khi chỉ cần một nhóm cột.
- Giữ schema tốt hơn CSV sau khi đã ép kiểu.
- Nén tốt và phù hợp cho dữ liệu trung gian nhiều bước.
- Spark hỗ trợ đọc/ghi Parquet và partition rất tốt.

Kết quả sau notebook 01:

| Dataset | Rows | Columns | Partition |
|---|---:|---:|---|
| Train | 1,708,337 | 61 | `session_year`, `session_month` |
| Test | 401,589 | 61 | `session_year`, `session_month` |

## 3. Notebook 01 - Read CSV To Parquet

Mục tiêu: chuyển raw CSV thành dữ liệu session-level dạng Parquet để các bước sau không phải parse CSV lại.

| Nội dung | Trình bày |
|---|---|
| Công cụ | PySpark, Spark SQL functions, Parquet writer |
| Đã làm | Đọc CSV, parse JSON, tạo cột session/date/time, chuẩn hóa numeric, tạo traffic/device/geo fields |
| Vấn đề cần xử lý | CSV nặng, nhiều cột nested JSON, kiểu dữ liệu chưa phù hợp |
| Cách xử lý | Parse JSON thành cột phẳng, ép kiểu, drop cột JSON gốc sau khi extract, ghi Parquet partition |
| Kết quả | Train/test Parquet, mỗi bảng 61 columns, partition theo `session_year`, `session_month` |

Output chính:

- `data_pyspark_parquet/train_sessions`
- `data_pyspark_parquet/test_sessions`
- `data_pyspark_parquet/read_csv_to_parquet_log.json`

## 4. Notebook 02 - Data Quality Check

Mục tiêu: tìm các vấn đề thật sự ảnh hưởng đến cleaning, labeling và modeling. Các check bình thường không cần đưa vào document.

| Issue | Số liệu | Vì sao là vấn đề | Cách xử lý ở bước sau |
|---|---:|---|---|
| Duplicate session key | Train 1,724 rows; test 477 rows | Làm sai timeline và user history | Dedupe trước khi tạo label/feature |
| Incomplete 30-day label window | Train 82,601 rows; test 71,168 rows | Không đủ tương lai 30 ngày để gán nhãn chắc chắn | Tạo `has_full_30d_label_window`, chỉ train/evaluate trên dòng đủ window |
| Placeholder/sparse columns | Nặng ở campaign, keyword, ad content, referral path, geo fields | Dùng giá trị thô sẽ gây nhiễu và tăng cardinality | Chuẩn hóa thành `unknown`/`other` hoặc chuyển thành flag |
| Revenue/transaction leakage candidates | Có ở các cột revenue/transaction hiện tại | Nếu dùng làm feature sẽ làm model nhìn thấy tín hiệu target | Chỉ dùng để tạo label/audit, exclude khỏi feature |

Kết quả sau notebook 02: có danh sách issue rõ ràng để đưa sang notebook clean/label, thay vì xử lý dữ liệu theo cảm tính.

## 5. Notebook 03 - Cleaning & Labeling

Mục tiêu: sửa các vấn đề data quality và tạo label tương lai 30 ngày.

| Nội dung | Trình bày |
|---|---|
| Công cụ | PySpark window, transformation, join theo user timeline, Parquet |
| Đã làm | Dedupe session, chuẩn hóa placeholder, tạo `has_full_30d_label_window`, tạo 2 target future 30 ngày |
| Vấn đề cần xử lý | Duplicate key, incomplete label window, leakage từ revenue source columns |
| Cách xử lý | Dedupe key; chỉ supervised training trên dòng đủ label window; đưa revenue source columns vào nhóm exclude |
| Kết quả | Clean/label output có 91 columns, lưu theo 5 column chunks, duplicate sau clean = 0 |

Target sau bước này:

- `future_30d_has_purchase`
- `future_30d_revenue`

Output chính:

- `data_pyspark_parquet/train_sessions_clean_30d_label`
- `data_pyspark_parquet/test_sessions_clean_30d_label`
- `data_pyspark_parquet/clean_30d_label_sessions_manifest.json`

## 6. Notebook 04 - EDA With PySpark

Mục tiêu: hiểu target, revenue, traffic/device/geo, engagement và user history trước khi tạo feature/model.

| Nội dung | Trình bày |
|---|---|
| Công cụ | PySpark aggregation, window summary, Pandas/plotting cho bảng aggregate nhỏ |
| Đã làm | Phân tích label window, target rate, revenue distribution, traffic/device/geo performance, engagement buckets, RFM/user history |
| Vấn đề cần xử lý | Positive rate rất thấp; revenue cực lệch; user history quan trọng nhưng dễ leakage |
| Cách xử lý | Chọn hướng two-stage model; dùng log transform cho revenue; tạo feature lịch sử chỉ dựa trên quá khứ |
| Kết quả | Insight phục vụ feature engineering và modeling |

Insight chính:

- Tỷ lệ mua hàng thấp nên bài toán classification bị imbalance.
- Revenue có phân phối lệch mạnh, đa số bằng 0 và một số ít session có revenue cao.
- Traffic channel, device, geo và engagement có khác biệt về conversion/revenue.
- Lịch sử user là nhóm tín hiệu quan trọng, nhưng phải tạo theo đúng thứ tự thời gian.

## 7. Notebook 05 - Feature Engineering

Mục tiêu: tạo feature table cuối cùng cho model, không null, không duplicate, không leakage.

| Nội dung | Trình bày |
|---|---|
| Công cụ | PySpark window, aggregation theo user timeline, Parquet |
| Đã làm | Tạo Feature Set gồm 27 feature |
| Vấn đề cần xử lý | Không được dùng tương lai khi tạo user history; train/test phải cùng schema; feature không được chứa label/leakage |
| Cách xử lý | Chỉ dùng previous sessions; chuẩn hóa categorical; validate schema/null/leakage bằng report |
| Kết quả | Feature table train/test khớp schema, null feature count = 0, leakage list = [] |

Nhóm feature chính:

| Nhóm | Ví dụ |
|---|---|
| Current session | `visit_number`, `totals_hits`, `totals_pageviews`, `session_hour`, `session_month` |
| Traffic/device/geo | `channelGrouping_model`, `traffic_channel_type_model`, `device_category_model`, `geo_country_model` |
| User history | `user_previous_sessions`, `user_previous_total_revenue`, `user_previous_purchase_count`, `has_previous_purchase` |

Kết quả feature validation:

| Dataset | Rows | Feature count | Duplicate key | Feature null |
|---|---:|---:|---:|---:|
| Train | 1,706,613 | 27 | 0 | 0 |
| Test | 401,112 | 27 | 0 | 0 |

Labeled rows dùng cho modeling:

| Dataset | Labeled rows | Positive purchase rate |
|---|---:|---:|
| Train | 1,624,078 | 1.31% |
| Test | 330,036 | 1.56% |

## 8. Notebook 06 - Modeling

Mục tiêu: train model dự đoán purchase probability và expected revenue.

| Nội dung | Trình bày |
|---|---|
| Công cụ | LightGBM classifier, LightGBM regressor, time-based validation split |
| Đã làm | Train classifier cho purchase; train regressor cho revenue nếu purchase; tính expected revenue |
| Vấn đề cần xử lý | Class imbalance, revenue skew, calibration revenue chưa tốt |
| Cách xử lý | Dùng `scale_pos_weight`; log transform revenue bằng `log1p`; đánh giá thêm revenue capture |
| Kết quả | Recall tốt và ranking expected revenue tốt hơn calibration |

Logic model:

```text
purchase_probability_30d = classifier(features)
predicted_revenue_if_purchase_30d = expm1(regressor(features))
expected_revenue_30d = purchase_probability_30d * predicted_revenue_if_purchase_30d
```

Classification result:

| Dataset | Accuracy | Precision | Recall |
|---|---:|---:|---:|
| Validation | 0.817 | 0.052 | 0.835 |
| Test | 0.782 | 0.056 | 0.816 |

> Số liệu là kết quả của pipeline sau khi đã finetune cả classifier lẫn regressor (mục 8.1, 8.2).

### 8.1 Finetune classifier (Grid Search + Optuna)

Hyperparameter tuning chạy theo đúng time-based split: mọi cấu hình đều fit trên train split và chấm điểm trên validation (không random CV). Metric chọn model là **PR-AUC** (average precision), phù hợp với target imbalance hơn accuracy; `scale_pos_weight` giữ cố định và dùng early stopping để tự chọn số cây. Tuning chạy thuần Pandas sau khi đã convert từ Spark (Spark `stop()` để giải phóng JVM, tránh OOM); Optuna chạy tuần tự (`n_jobs=1`) để LightGBM tự dùng hết core.

| Phương pháp | PR-AUC (validation) | Ghi chú |
|---|---:|---|
| Baseline (base params) | 0.073 | Tham chiếu |
| Grid Search (16 tổ hợp) | 0.125 | `num_leaves=31, learning_rate=0.1, min_child_samples=20, colsample_bytree=0.7, n_estimators=143` |
| Optuna (TPE, 30 trials) | **0.130** | Bộ params được chọn (winner) |

Optuna best params: `num_leaves=22, learning_rate=0.134, min_child_samples=64, subsample=0.883, colsample_bytree=0.608, reg_lambda=7.58, n_estimators=225`. Final classifier dùng bộ params này — PR-AUC trên validation tăng ~78% so với baseline reference.

### 8.2 Finetune regressor (Grid Search + Optuna)

Cùng nguyên tắc time-based split, nhưng chỉ fit trên **positive-revenue rows** của train và chấm điểm trên validation positive rows. Metric chọn model là **RMSE log scale** (càng nhỏ càng tốt), đúng target `log1p(future_30d_revenue)`; có early stopping để tự chọn số cây.

| Phương pháp | RMSE log (validation) | Ghi chú |
|---|---:|---|
| Baseline (base params) | 1.054 | Tham chiếu |
| Grid Search (16 tổ hợp) | 1.051 | `num_leaves=15, learning_rate=0.1, min_child_samples=20, colsample_bytree=0.9, n_estimators=91` |
| Optuna (TPE, 30 trials) | **1.049** | Bộ params được chọn (winner) |

Optuna best params: `num_leaves=33, learning_rate=0.105, min_child_samples=16, subsample=0.806, colsample_bytree=0.837, reg_lambda=0.0015, n_estimators=25`. Optuna thắng nhưng **biên độ rất nhỏ** (RMSE log giảm ~0.4% so với baseline): tín hiệu revenue ở positive rows gần như đã bão hòa với feature set hiện tại, nên muốn cải thiện lớn cần thêm feature thay vì tune sâu hơn.

Expected revenue ranking:

| Dataset | Top 10% revenue capture |
|---|---:|
| Validation | 71.07% |
| Test | 82.48% |

Kết luận modeling: model phù hợp hơn để ranking/ưu tiên user-session có giá trị cao. Predicted average expected revenue đang cao hơn actual average, nên chưa nên xem expected revenue là dự báo tiền tuyệt đối đã calibration tốt.

## 9. API Serving System

Phần API chỉ là bước đóng gói model để demo cách hệ thống có thể phục vụ prediction trong thực tế. Vì đây là local/offline project.
### Công cụ dùng trong API

| Công cụ | Lý do dùng |
|---|---|
| FastAPI | Tạo REST API nhanh, có Swagger UI tại `/docs` |
| Pydantic | Validate input/output schema |
| PyArrow Dataset | Lookup session trong Parquet feature table mà không load toàn bộ vào RAM |
| pandas | Chuẩn bị một dòng feature đúng format cho LightGBM |
| LightGBM model `.pkl` | Dùng lại classifier/regressor đã train |
| In-memory cache | Giảm lookup/predict lặp lại trong demo local |

### Luồng hoạt động

```text
Request visitor_id + session_id
-> validate schema
-> lookup feature row trong Parquet
-> chuẩn hóa 27 feature theo metadata
-> classifier predict purchase probability
-> regressor predict revenue if purchase
-> tính expected revenue
-> trả session info + model info + prediction
```

Endpoint chính:

| Endpoint | Mục đích |
|---|---|
| `GET /health` | Kiểm tra API/model/cache |
| `GET /model/info` | Xem model version, threshold, feature count, metrics |
| `POST /sessions/lookup` | Lookup session và feature |
| `POST /predict/session` | Predict live cho một session |
| `GET /cache/status` | Xem trạng thái cache |
| `POST /cache/clear` | Xóa cache |

### Cache trong API

Cache là bộ nhớ tạm để tránh làm lại việc giống nhau.

| Cache | Dùng để làm gì |
|---|---|
| Model cache | Load classifier, regressor và metadata một lần khi API startup |
| Feature lookup cache | Lưu feature row theo `(dataset, visitor_id, visit_id)` |
| Prediction cache | Lưu full prediction response theo model version và session key |

Vấn đề API còn hạn chế:

- Chỉ predict được session đã tồn tại trong feature table.
- Chưa nhận raw session mới để tự tạo feature online.
- Cache là in-memory nên restart API sẽ mất cache.
- Chưa có authentication, monitoring, model registry.

## 10. Kết luận

Pipeline hiện tại đã đi qua flow chính của một bài toán DS thực tế:

1. Xác định bài toán và target.
2. Chuyển raw CSV sang Parquet bằng PySpark.
3. Kiểm tra data quality và xử lý issue quan trọng.
4. Clean, dedupe và tạo label future 30 ngày.
5. EDA để hiểu dữ liệu và định hướng feature/model.
6. Tạo Feature Set không leakage.
7. Train LightGBM two-stage model.
8. Tạo API để demo serving.

Kết quả chính:

- CSV đã được chuyển sang Parquet với 61 columns.
- Clean/label output có 91 columns và duplicate sau clean = 0.
- Feature Set có 27 feature, schema match true, feature null count = 0.
- Test recall đạt 0.816; top 10% expected revenue capture đạt 82.48% (sau khi finetune classifier + regressor).
- API có thể lookup session, trả feature, model metadata và prediction.
