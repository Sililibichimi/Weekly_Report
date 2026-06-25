### Các nhiệm vụ cần thực hiện với bài toán :

0. Khung bài toán & validation

Chốt metric: precision@800 / lift, kèm AUC để so sánh model.
Tách validation set theo stratified (giữ tỷ lệ 6%). Cân nhắc k-fold vì lớp dương chỉ 348 mẫu → hold-out đơn lẻ dễ nhiễu

1. Data quality check
Kiểm tra dữ liệu trống, kiểu dữ liệu, miền giá trị, các cột, ...
Kiểm tra trùng lặp dữ liệu
Kiểm tra business rule(nếu cần)

2. Data cleaning
Với các vấn đề nêu trên thì đưa ra cách xử lý tương ứng.
3. EDA
Phân tích target để trình bày vấn đề imbalance
Với mỗi feature: phân tích dựa trên target/lift theo với từng giá trị

4. Feature engineering
Xử lý các feauter bằng các phương pháp WoE, ...
Loại bỏ các thuộc tính dư thừa
5. Baseline -> Modeling
Train model cơ bản,
Train các model với dữ liệu được xử lý bằng các phương pháp khác nhau 

6. Đánh giá
Đo validation bằng metric đã chốt

7. Feature Importance
Đánh giá feature importance

8. Finetune
Tune hyperparameter để đưa ra mô hình cuối

9. Runtest
Áp dụng luông với dữ liệu test và chạy model với dữ liệu test để đưa ra kết quả cuối.
