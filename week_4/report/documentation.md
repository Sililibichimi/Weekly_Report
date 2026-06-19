# Project Documentation - Week 4: Cải thiện model Future 30D Purchase & Revenue

Tiếp nối week_3 (đã hoàn thành pipeline tới modeling baseline + API), week_4 tập trung **cải thiện model**
qua 4 bước: feature importance → thêm feature mới → xử lý mất cân bằng → finetune & chốt model trên test.

## 1. Bối cảnh & mục tiêu

| Nội dung | Trình bày |
|---|---|
| Bài toán | Tại mỗi session, dự đoán user có mua trong 30 ngày tới (classification) và doanh thu kỳ vọng (regression) |
| Điểm xuất phát | Model baseline week_3: LightGBM 2 tầng, feature V1 (27 feature), xử lý imbalance bằng `scale_pos_weight` |
| Mục tiêu week_4 | (1) hiểu feature nào quan trọng, (2) thử thêm feature, (3) thử các cách xử lý imbalance, (4) finetune model mới |
| Nguyên tắc | Fit/tune/chọn threshold **chỉ trên train + validation**; test chỉ chạy 1 lần khi đã chốt model |
| Metric chính | **PR-AUC** (average precision) cho classifier — phù hợp dữ liệu lệch hơn accuracy; **RMSE-log** cho regressor |

Phân phối label rất lệch: positive (có mua trong 30 ngày) chỉ ~1.3% trên train, ~1.2% trên validation.

## 2. Notebook 07 - Feature Importance

Mục tiêu: tạo **mốc tham chiếu** trước khi thêm feature/đổi cách xử lý imbalance.

| Nội dung | Trình bày |
|---|---|
| Công cụ | LightGBM built-in importance (`gain`, `split`) + **permutation importance** trên validation |
| Đã làm | Xếp hạng 27 feature V1 cho cả classifier và regressor |
| Vấn đề cần xử lý | `gain` thiên vị feature high-cardinality (vd `geo_country_model`) |
| Cách xử lý | Ưu tiên permutation importance (đo trực tiếp tác động lên metric khi xáo trộn feature) |
| Kết quả | Lõi model: `visit_number`, `totals_hits`, `totals_pageviews`, nhóm user-history |

Bộ feature **V1 baseline (27 feature)** kế thừa từ week_3, chia theo nhóm:

| Nhóm | Feature |
|---|---|
| Current-session numeric/time (9) | `visit_number`, `totals_hits`, `totals_pageviews`, `totals_time_on_site`, `totals_new_visits`, `is_bounce`, `session_hour`, `session_day_of_week`, `session_month` |
| Categorical (4) | `channelGrouping_model`, `traffic_channel_type_model`, `device_category_model`, `geo_country_model` |
| Sparse flags (3) | `has_gclid`, `has_traffic_campaign`, `has_referral_path` |
| User-history (9) | `user_previous_sessions`, `user_days_since_first_session`, `user_days_since_previous_session`, `user_previous_avg_pageviews`, `user_previous_avg_time_on_site`, `user_previous_bounce_rate`, `user_previous_purchase_count`, `user_previous_total_revenue`, `user_days_since_previous_purchase` |
| Derived flags (2) | `is_first_session`, `has_previous_purchase` |

Feature **yếu** (permutation ≤ 0, gần như không đóng góp cho classifier) — ứng viên loại bỏ ở Bước 4:
`session_month`, `is_first_session`, `is_bounce`, `has_gclid`, `has_traffic_campaign`, `has_previous_purchase`.

Output: `week_4/feature_importance_outputs/` (bảng built-in + permutation importance).

## 3. Notebook 08 - Thêm Feature V2

Mục tiêu: thử thêm feature V2 (categorical chi tiết + sparse flags) xem có cải thiện model không.

| Nội dung | Trình bày |
|---|---|
| Công cụ | PyArrow đọc bảng nguồn theo chunk cột; join `fullVisitorId + visit_id`; rare-category bucketing |
| Đã làm | Thêm 14 feature V2 (4 categorical + 10 flag) vào bộ V1 → tổng 41 feature |
| Vấn đề cần xử lý | High-cardinality (`traffic_source_clean_model`); tránh leakage; so sánh phải công bằng |
| Cách xử lý | Gom category hiếm (`count < 200`) thành `__other__` (**fit train-only**); test chỉ transform; so PR-AUC (không phụ thuộc threshold) |
| Kết quả | V2 **không cải thiện classifier**; giúp regressor một chút |

Feature V2 thêm:

| Nhóm | Feature |
|---|---|
| Categorical | `traffic_source_clean_model`, `traffic_medium_clean_model`, `browser_family_model`, `os_family_model` |
| Sparse flags | `is_direct_traffic`, `is_paid_traffic`, `is_organic_traffic`, `is_referral_traffic`, `has_traffic_keyword`, `has_traffic_ad_content`, `has_geo_region`, `has_geo_metro`, `has_custom_dimension`, `is_socially_engaged` |

So sánh classifier (cùng threshold 0.5):

| Bộ feature | PR-AUC | recall@0.5 | precision@0.5 |
|---|---:|---:|---:|
| V1 | 0.1264 | 0.828 | 0.051 |
| V1 + V2 | 0.1249 | 0.854 | 0.052 |

> Bài học: so sánh feature phải dùng metric **không phụ thuộc threshold** (PR-AUC). Recall đơn lẻ gây hiểu nhầm
> vì nó chỉ phản ánh threshold đang chọn, không phản ánh chất lượng model.

Output: `week_4/feature_v2_outputs/` + bảng mở rộng `train/test_user_session_features_30d_v2.parquet`.

## 4. Notebook 09 - Xử lý mất cân bằng

Mục tiêu: thử các phương pháp cân bằng và đo bằng số, trên **cùng một validation set cố định**.

| Nội dung | Trình bày |
|---|---|
| Công cụ | `imbalanced-learn` (SMOTENC), random under/over-sampling tự code bằng pandas |
| Đã làm | So 6 chiến lược: baseline `scale_pos_weight`, no_handling, under 1:1, under 1:5, over 1:1, SMOTENC |
| Vấn đề cần xử lý | Chỉ resample **train split**; bỏ `scale_pos_weight` khi đã resample (tránh cân bằng 2 lần); SMOTE thuần không xử lý categorical |
| Cách xử lý | Validation giữ phân phối thật; dùng **SMOTENC** cho dữ liệu mixed; chọn theo PR-AUC |
| Kết quả | **Không** phương pháp nào cải thiện ranking; train phân phối thật là tốt nhất |

Kết quả (xếp theo PR-AUC validation):

| Chiến lược | PR-AUC | recall@0.5 | precision@0.5 | train rows |
|---|---:|---:|---:|---:|
| **no_handling** (phân phối thật) | **0.1385** | 0.007 | 0.471 | 1.53M |
| over 1:1 | 0.1300 | 0.852 | 0.052 | 3.02M |
| under 1:5 | 0.1292 | 0.579 | 0.102 | 0.12M |
| baseline `scale_pos_weight` | 0.1249 | 0.854 | 0.052 | 1.53M |
| SMOTENC (ratio 0.3) | 0.1246 | 0.009 | 0.370 | 1.96M |
| under 1:1 | 0.1179 | 0.881 | 0.049 | 0.04M |

> Phát hiện: `scale_pos_weight`/oversampling chỉ **dịch ngưỡng hiệu dụng** (đẩy recall@0.5 lên) chứ không
> giúp model tách lớp tốt hơn. Với LightGBM trên dữ liệu lệch, **chọn threshold** mới là chìa khóa, không phải resampling.

Output: `week_4/imbalance_outputs/` (bảng so sánh + biểu đồ PR-AUC).

## 5. Notebook 10 - Finetune & chốt model

Mục tiêu: finetune model mới trên bộ feature đã chốt + train phân phối thật, rồi đánh giá test.

| Nội dung | Trình bày |
|---|---|
| Công cụ | Optuna (TPE sampler) + early stopping; LightGBM classifier & regressor |
| Đã làm | Lọc feature yếu (41 → 33); finetune 2 model; chọn threshold; final test |
| Vấn đề cần xử lý | Tránh ship model tệ hơn baseline; threshold cho dữ liệu lệch; không leak test |
| Cách xử lý | **Enqueue cấu hình baseline** vào Optuna (best ≥ baseline); chọn threshold F1-optimal trên validation; test chạy 1 lần cuối |
| Kết quả | Classifier PR-AUC tăng nhẹ, regressor RMSE-log giảm; test generalize tốt |

Bộ feature dùng: **V1+V2 lọc bớt** = 33 feature (bỏ 8 feature yếu từ NB07/NB08). Đã kiểm chứng lọc **không làm hại**:
PR-AUC classifier 0.1385 (full) → 0.1418 (lọc), tức lọc còn **tốt hơn**.

### 5.0 Feature changelog (bỏ gì / thêm gì / giữ gì)

Diễn biến số lượng feature qua 4 bước:

| Mốc | Số feature | Thay đổi |
|---|---:|---|
| V1 baseline (week_3) | 27 | điểm xuất phát |
| + V2 (NB08) | 41 | **thêm 14** (4 categorical + 10 flag) |
| − feature yếu (NB10) | **33** | **bỏ 8** (permutation ≤ 0) |

**8 feature bị BỎ** (kèm lý do & nguồn):

| Feature | Nhóm gốc | Lý do | Phát hiện ở |
|---|---|---|---|
| `session_month` | V1 time | permutation ≤ 0 với classifier | NB07 |
| `is_first_session` | V1 derived flag | trùng tín hiệu với `user_previous_sessions` | NB07 |
| `is_bounce` | V1 session | permutation ≤ 0 | NB07 |
| `has_gclid` | V1 flag | permutation ≤ 0 | NB07 |
| `has_traffic_campaign` | V1 flag | permutation ≤ 0 | NB07 |
| `has_previous_purchase` | V1 derived flag | trùng tín hiệu với `user_previous_purchase_count` | NB07 |
| `is_socially_engaged` | V2 flag | permutation ≈ 0, gần như hằng số | NB08 |
| `is_organic_traffic` | V2 flag | permutation ≤ 0; đã có `traffic_channel_type_model` | NB08 |

**14 feature được THÊM ở V2** — xem bảng chi tiết ở mục 3 (4 categorical: `traffic_source_clean_model`,
`traffic_medium_clean_model`, `browser_family_model`, `os_family_model`; 10 sparse flags traffic/geo/social).
Trong đó 12/14 được **giữ lại** sau lọc, chỉ 2 flag (`is_socially_engaged`, `is_organic_traffic`) bị loại.

**33 feature CUỐI CÙNG** (bộ dùng để finetune & deploy):

| Nhóm | Feature |
|---|---|
| Current-session numeric/time (7) | `visit_number`, `totals_hits`, `totals_pageviews`, `totals_time_on_site`, `totals_new_visits`, `session_hour`, `session_day_of_week` |
| Categorical (8) | `channelGrouping_model`, `traffic_channel_type_model`, `device_category_model`, `geo_country_model`, `traffic_source_clean_model`, `traffic_medium_clean_model`, `browser_family_model`, `os_family_model` |
| Sparse flags (9) | `has_referral_path`, `is_direct_traffic`, `is_paid_traffic`, `is_referral_traffic`, `has_traffic_keyword`, `has_traffic_ad_content`, `has_geo_region`, `has_geo_metro`, `has_custom_dimension` |
| User-history (9) | `user_previous_sessions`, `user_days_since_first_session`, `user_days_since_previous_session`, `user_previous_avg_pageviews`, `user_previous_avg_time_on_site`, `user_previous_bounce_rate`, `user_previous_purchase_count`, `user_previous_total_revenue`, `user_days_since_previous_purchase` |

### 5.1 Finetune classifier (Optuna, tối ưu PR-AUC)

Mọi cấu hình fit trên train split, chấm điểm `average_precision` trên validation, early stopping tự chọn số cây.
KHÔNG dùng `scale_pos_weight` (theo kết luận NB09).

| Phương pháp | PR-AUC (validation) | Ghi chú |
|---|---:|---|
| Baseline lọc (base params) | 0.1418 | Tham chiếu (đã enqueue vào Optuna) |
| Optuna (TPE, 30 trials) | **0.1425** | Winner |

Best params: `learning_rate=0.043, num_leaves=33, max_depth=11, min_child_samples=205, subsample=0.74, colsample_bytree=0.80, reg_lambda=0.028, reg_alpha=1.39`; `best_iteration=448`.

### 5.2 Finetune regressor (Optuna, tối ưu RMSE-log)

Chỉ fit trên **positive-revenue rows**, target `log1p(future_30d_revenue)`.

| Phương pháp | RMSE-log (validation) | Ghi chú |
|---|---:|---|
| Baseline lọc (base params) | 1.0545 | Tham chiếu |
| Optuna (TPE, 30 trials) | **1.0370** | Winner |

Best params: `learning_rate=0.014, num_leaves=239, max_depth=11, min_child_samples=47, subsample=0.66, colsample_bytree=0.96, reg_lambda=0.038, reg_alpha=2.85`; `best_iteration=113`.

### 5.3 Chọn threshold

Dữ liệu lệch → threshold 0.5 không hợp lý. Quét PR-curve, chọn **F1-optimal = 0.127** trên validation.
Báo cáo kèm các điểm vận hành khác (top 1%/5% theo điểm) để chọn theo nhu cầu marketing.

### 5.4 Final Test Evaluation (chốt model)

Sau khi chốt feature + params + threshold mới đụng test (không refit, không chọn lại threshold).

| Metric | Validation | Test |
|---|---:|---:|
| PR-AUC | 0.1425 | **0.1567** |
| Precision @0.127 | 0.171 | 0.183 |
| Recall @0.127 | 0.277 | 0.286 |
| F1 @0.127 | 0.211 | 0.223 |
| Accuracy | 0.976 | 0.969 |
| Conditional RMSE-log | 1.037 | 1.095 |

Expected revenue ranking (revenue capture):

| | Top 1% | Top 5% | Top 10% |
|---|---:|---:|---:|
| Validation | 25.7% | 61.1% | 77.8% |
| Test | 56.3% | 75.3% | **84.8%** |

> Test generalize tốt (PR-AUC test còn cao hơn validation). Giống week_3, model mạnh nhất ở vai trò **ranking**
> user-session giá trị cao: top 10% theo expected revenue thu được ~85% tổng doanh thu thực tế trên test.

Output: model lưu ở `models/finetuned_<version>/` (2 file `.pkl` + `finetune_metadata.json` + `final_test_metrics.json`).

## 6. Vệ sinh dữ liệu (data hygiene)

| Bước | Fit từ đâu | Test dùng để |
|---|---|---|
| Rare-category mapping & category levels (NB08) | train | chỉ transform |
| Filtering check / Optuna scoring (NB10) | train split (fit), validation (score) | không dùng |
| Chọn threshold (NB10) | validation | không dùng |
| Final test (NB10 mục 9) | — | chỉ predict 1 lần, không refit |

→ Không có rò rỉ test vào quá trình fit/tune/chọn threshold.

## 7. Kết luận

| Bước | Kết luận |
|---|---|
| Feature importance | `visit_number`, `totals_hits`, user-history là lõi; 8 feature yếu nên loại |
| Feature V2 | Không cải thiện classifier (PR-AUC); chỉ giúp regressor nhẹ |
| Imbalance | Resampling/`scale_pos_weight` không cải thiện ranking; train phân phối thật + chọn threshold đúng hướng |
| Finetune | Lọc feature giúp PR-AUC tăng; Optuna + enqueue baseline đảm bảo không tệ hơn baseline |

Model week_4 (V1+V2 lọc, Optuna, phân phối thật, threshold 0.127) đạt **PR-AUC test 0.157**,
**top 10% revenue capture 84.8%** — sẵn sàng thay thế model baseline week_3 trong API
(trỏ tới `models/finetuned_<version>/`, đọc `selected_threshold` và `feature_columns` từ metadata).
