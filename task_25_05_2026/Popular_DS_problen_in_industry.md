Các dạng bài toán chính là :
- Bài toán phân loại (Classification)
- Bài toán hồi quy (Regression)
- Bài toán ranking (Ranking)
- Bài toán phân cụm (Clustering)
- Bài toán dự báo (Forecasting)
- Phát hiện bất thường (Anomaly detection)
- Đo lường tác động (Causal Inference/Experiment)
- Bài toán tối ưu (Optimization)

Các bài toán chính :
- Churn prediction : Dự đoán khách hàng rời bỏ.
	Bài toán này trả lời câu hỏi : Khách hàng nào có khả năng ngừng dịch vụ/ sản phẩm
	Dữ liệu thường dùng như: Số lần đăng nhập, tần suất mua hàng, số ticket support, số lỗi gặp, lịch sử thanh toán...
	Các mô hình thường dùng để dự đoán như: Logistics regression, Random forest, XGBoost/LightGBM, ...
	Các metrics thường dùng: Precision, Recall, F1-score, ROC-AUC, PR-AUC
	-> Đưa ra các hành động như: gửi voucher, chăm sóc riêng, ...

- Fraud Detection: phát hiện gian lận
	+ Bài toán trả lời câu hỏi: Giao dịch hay hành vi nào có dấu hiệu gian lận
	+ Dữ liệu dựa trên lịch sử giao dịch, hành vi, thời gian, thiết bị, ...
	+ Bài toán có thể là: Phân loại hay phát hiện bất thường
	+ Mô hình thường dùng: LR, Random forest, SVM,
	+ Metric thường dùng: Precision, recall, F1-score, PR-AUC,
	+ Trong bài toán này, do dữ liệu thường bị mất cân bằng, số nhãn không gian lận thường lớn hơn rất nhiều so với nhãn có. Vì vậy thường không dùng accuracy để đánh giá.

- Recommendation system: Hệ thống gợi ý
	+ Bây giờ ta sẽ phải gợi ý gì cho khách hàng?
	+ Dữ liệu thường dùng: Lịch sử mua hàng, click, sản phẩm đã xem, tìm kiếm, ...
	+ Các bài toán ML:
		. Collaborative Filtering: Ví dụ User A và User B cùng thích nhiều sản phẩm giống nhau. Nếu B thích sản phẩm X mà A chưa mua, thì gợi ý X cho A.
		. Ranking problem : Không chỉ đoán là user thích gì, còn phải xếp hạng các sản phẩm đó.
		. Content-based Filtering: Dựa trên các đặc điểm của sản phẩm để đưa ra gợi ý.
	+ Các model: KNN, LR, Gradient Boosting, Learning to rank, ...
	+ Metric đánh giá: Precision@K, Recall@K, NDCG@K, MAP@K, CTR uplift, ...

- Forecasting - Dự báo theo thời gian
	+ Điều gì sẽ xảy ra trong tương lai?
	+ Dữ liệu thường dùng: Dữ liệu theo ngày, theo tuần, doanh thu lịch sử, đơn hàng lịch sử, ...
 	+ Bài toán thường là: time series forecasting.
	+ Model thường dùng: Moving Average, Exponential Smoothing, ARIMA/ SARIMA, prophet, XGBoosting/LightGBM với feature thời gian.
	+ Metric đánh giá: MAE, RMSE, MAPE, sMAPE, WAPE

- Customer Segmentation: Phân nhóm khách hàng
	+ Có những nhóm khách hàng nào, và mỗi nhóm nên được chăm sóc như nào?
	+ Dữ liệu thường dùng: Lần mua gần đây, giá trị mua hàng, loại hàng, ....
	+ Thường là các bài toán phân cụm
	+ Model thường dùng: K-means, DBScan, PCA/UMAP để giảm chiều, ...
	+ Metric: Silhouette Score, Davies-Bouldin Index, Business interpretability, ...

- Leading Scoring/ Propensity Modeling
	+ Ai có khả năng chuyển đổi cao nhất? Ví dụ khách hàng nào có khả năng mua premium
	+ Dữ liệu: Nguồn lead, số lần truy cập web, form, ...
	+ Bài toán thường là phân loại hoặc ranking.
	+ Model thường dùng như LR, Decision tree, Random forest, ..
	+ metric : ROC-AUC, PR-AUC, lift chart, ...

- Pricing Optimization: Tối ưu giá
	+ Nên đặt giá bao nhiêu để tối đa doanh thu hoặc lợi nhuân?
	+ Dữ liệu thường là: Giá lịch sử, Chi phí, Giá đối thủ, ...
	+ Bài toán có thể là: Regression, Demand estimation, Optimization,

- Customer Lifetime Value: Dự đoán vòng đời khách hàng
	+ Một khách hàng có thể đem lại giá trị bao nhiêu trong tương lai.

