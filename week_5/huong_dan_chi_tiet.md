# Hướng dẫn học chi tiết — Phase 0 → 3 (Nền tảng → EDA)

> Cách dùng: đọc từng nhiệm vụ, tự gõ lại code (đừng copy-paste cả khối), chạy, rồi
> đối chiếu với phần **✅ Kết quả mong đợi** để biết mình làm đúng chưa.
> Mỗi nhiệm vụ có **🎯 Học gì → ❓ Tại sao → 🔧 Làm gì → 💻 Code gợi ý → 👀 Cần quan sát → ⚠️ Bẫy**.

## Chuẩn bị môi trường

```bash
pip install pandas numpy scikit-learn matplotlib seaborn
```

```python
import pandas as pd, numpy as np
import matplotlib.pyplot as plt, seaborn as sns

# Header file = ID,1,2,...,86  -> ten cot la chuoi '1'..'86'
df = pd.read_csv("Data/train_data.txt")
TARGET = "86"
FEATURES = [c for c in df.columns if c not in ("ID", TARGET)]
print(df.shape)          # (5822, 87)
print(df[TARGET].mean()) # ~0.0598
```

---

# PHASE 0 — Khung bài toán & validation

## 0.1 — Hiểu đây là bài toán *ranking*, không phải phân loại

**🎯 Học gì:** phân biệt classification (đoán nhãn 0/1) vs ranking (xếp hạng theo xác suất rồi lấy top-k).

**❓ Tại sao:** đề yêu cầu "lọc **800** người tiềm năng nhất trong 4000". Ta không cần biết chính xác ai mua/không, chỉ cần **xếp hạng đúng** để 800 người đầu bảng chứa nhiều người mua nhất. Vì vậy model phải xuất **xác suất** (`predict_proba`), và ta cắt ở top-800.

**🔧 Làm gì:** ghi nhớ — output cuối là `score` (xác suất) → sort giảm dần → lấy 800 ID đầu.

## 0.2 — Chọn metric đúng

**🎯 Học gì:** `precision@k`, `lift@k`, AUC; và vì sao accuracy vô dụng ở đây.

**❓ Tại sao:** chỉ 6% người mua. Một model "đoán không mua hết" đạt accuracy 94% nhưng **vô dụng**. Ta cần metric đo "trong nhóm ta chọn, tỷ lệ mua cao tới đâu".

- **precision@k** = (số người THỰC SỰ mua trong top-k) / k.
- **lift@k** = precision@k / base_rate. Lift = 2.0 nghĩa là nhóm ta chọn mua gấp đôi trung bình.
- **Ánh xạ về validation:** test chọn 800/4000 = **top 20%**. Nên trên tập validation cỡ `n`, ta đánh giá **precision@top-20%** (k = 0.2·n) cho tương đương.
- **AUC / PR-AUC:** để so sánh tổng thể giữa các model.

**💻 Code gợi ý:**
```python
def precision_at_k(y_true, y_score, k):
    idx = np.argsort(y_score)[::-1][:k]   # k chi so co score cao nhat
    return y_true[idx].mean()

def lift_at_k(y_true, y_score, k):
    base = y_true.mean()
    return precision_at_k(y_true, y_score, k) / base

# vi du dung tren validation: k = 20% so dong
```

**⚠️ Bẫy:** đừng tối ưu accuracy/F1 mặc định của sklearn. Luôn quy về precision@top-20% hoặc lift.

## 0.3 — Thiết lập validation chống nhiễu & chống leakage

**🎯 Học gì:** Stratified K-Fold; khái niệm **data leakage**.

**❓ Tại sao:**
- Chỉ **348 mẫu dương** → nếu chia hold-out 1 lần, mỗi fold quá ít người mua → kết quả dao động mạnh. **K-Fold** lấy trung bình nhiều lần → ổn định. **Stratified** giữ đúng 6% ở mỗi fold.
- **Leakage** = vô tình để thông tin của tập validation/test "lọt" vào lúc train (vd tính WoE/target-encoding trên toàn bộ data rồi mới chia). Khi đó điểm validation đẹp giả tạo, ra test thật thì sụp.

**💻 Code gợi ý:**
```python
from sklearn.model_selection import StratifiedKFold
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

X, y = df[FEATURES], df[TARGET].values
for tr, va in skf.split(X, y):
    X_tr, X_va = X.iloc[tr], X.iloc[va]
    y_tr, y_va = y[tr], y[va]
    # ⚠️ MOI bien doi (WoE, target-encode, scaler) fit tren X_tr, transform X_va
    break
```

**👀 Cần quan sát:** in `y_tr.mean()` và `y_va.mean()` — cả hai phải ≈ 0.06 (nhờ stratify).

**✅ Kết quả mong đợi Phase 0:** base rate = **5.98%** (348/5822). Bạn có hàm `precision_at_k`, `lift_at_k` và một splitter dùng lại xuyên suốt.

---

# PHASE 1 — Data quality check

## 1.1 — Kiểm tra cơ bản: thiếu / kiểu / hình dạng / miền giá trị

**🎯 Học gì:** các "chiều" chất lượng dữ liệu (completeness, validity, consistency).

**🔧 Làm gì:** kiểm tra missing, dtype, số cột mỗi dòng, miền giá trị có khớp `attributes_description.pdf` không.

**💻 Code gợi ý:**
```python
print(df.isna().sum().sum())          # so o trong
print(df.dtypes.value_counts())       # nen toan int64
print(df["1"].min(), df["1"].max())   # subtype: 1..41
print(df["4"].min(), df["4"].max())   # avg age bin: 1..6
print(df["5"].min(), df["5"].max())   # main type: 1..10
```

**✅ Kết quả mong đợi:** 0 ô thiếu; tất cả int; miền giá trị nằm đúng mô tả.

## 1.2 — Trùng lặp & nhãn mâu thuẫn (quan trọng)

**🎯 Học gì:** phân biệt "trùng lặp lỗi" vs "trùng lặp hợp lệ"; khái niệm **Bayes/irreducible error** (trần độ chính xác).

**❓ Tại sao:** socio (cột 1–42) là dữ liệu *cấp zip-code* → nhiều khách trùng nhau là **bình thường**, KHÔNG xóa. Nhưng nếu hai dòng **trùng feature mà khác nhãn** → không model nào phân biệt nổi → đó là "trần" sai số. Đo nó để biết kỳ vọng thực tế.

**💻 Code gợi ý:**
```python
dup = df.duplicated(subset=FEATURES).sum()
print("Dong trung feature:", dup)      # ~651

g = df.groupby(FEATURES)[TARGET].nunique()
conflict_groups = (g > 1).sum()
print("Nhom feature co ca 0 lan 1:", conflict_groups)   # ~49
```

**👀 Cần quan sát:** ~651 dòng trùng feature; **49 nhóm (≈115 dòng)** nhãn mâu thuẫn → trần sai số **< 2%** → data **tách lớp tốt**, tín hiệu tốt. *Ghi câu này vào báo cáo.*

## 1.3 — Business rule (tùy chọn)

**🎯 Học gì:** kiểm tra ràng buộc logic của domain.

**🔧 Làm gì:** các nhóm % "compositional" (vd tôn giáo cột 6–9, giáo dục 16–18) có cộng về cùng một tổng trong mỗi vùng không. Nếu có → khẳng định chúng là dữ liệu tỷ lệ → cảnh báo đa cộng tuyến cho sau này.

**✅ Kết quả mong đợi Phase 1:** một "biên bản chất lượng" ngắn: data sạch, không cần impute, giữ trùng lặp, trần sai số nhỏ.

---

# PHASE 2 — Data cleaning

> Ở bài này cleaning **rất nhẹ** (không có missing). Việc chính là *chuẩn hóa hiểu biết về biến* để dùng lại.

## 2.1 — Lập "từ điển kiểu biến"

**🎯 Học gì:** vì sao "trông là số" chưa chắc là numeric; phân loại nominal / ordinal / count.

**❓ Tại sao:** encoding & model phụ thuộc hoàn toàn vào việc này. Cột 1 (subtype) và 5 (main type) là **nominal** (số không có thứ tự) → không được để model tuyến tính hiểu "41 > 1". Phần lớn còn lại là **ordinal** (đã binned 0–9). Cột 65–85 là **count**.

**💻 Code gợi ý:**
```python
NOMINAL = ["1", "5"]                 # ma danh muc, khong co thu tu
COUNT   = [str(i) for i in range(65, 86)]   # so luong policy
ORDINAL = [c for c in FEATURES if c not in NOMINAL + COUNT]
# luu lai dict nay, dung xuyen suot
```

**⚠️ Bẫy:** nhồi cột nominal vào logistic/KNN như số → model hiểu sai hoàn toàn.

## 2.2 — Đánh dấu cột gần hằng số

**🎯 Học gì:** feature gần như không đổi thì gần như vô dụng.

**💻 Code gợi ý:**
```python
near_const = [c for c in FEATURES
              if df[c].value_counts(normalize=True).iloc[0] > 0.99]
print("Cot gan hang so:", near_const)
```

**👀 Cần quan sát:** nhiều cột sản phẩm có >99% giá trị = 0 → ứng viên loại bỏ (để phase 4 quyết định).

## 2.3 — Quyết định xử lý

**🔧 Làm gì (ghi rõ lựa chọn):**
- Missing: không có → bỏ qua.
- Trùng lặp: **GIỮ** (khách hàng thật).
- Nhãn mâu thuẫn: **GIỮ** (chính là noise floor).
- Cột gần hằng: đánh dấu, cân nhắc bỏ ở FE.

**✅ Kết quả mong đợi Phase 2:** dict `NOMINAL/ORDINAL/COUNT` + danh sách `near_const`. Chưa biến đổi gì cả (biến đổi để phase 4).

---

# PHASE 3 — EDA

> Mục tiêu **kép**: (a) hiểu data để model; (b) tạo vật liệu cho **Task 2** (chân dung khách hàng).

## 3.1 — Phân tích target (imbalance)

**🎯 Học gì:** trực quan hóa & phát biểu vấn đề mất cân bằng.

**💻 Code gợi ý:**
```python
df[TARGET].value_counts().plot(kind="bar")
print(df[TARGET].mean())   # 0.0598
```

**👀 Cần quan sát:** 348 mua / 5474 không → 5.98%. Liên hệ: vì sao chọn metric ranking (Phase 0).

## 3.2 — Univariate theo target: bảng LIFT (lõi của EDA này)

**🎯 Học gì:** đọc sức mạnh dự báo của 1 feature qua **target rate** từng giá trị.

**❓ Tại sao:** với categorical/ordinal, lift cho thấy ngay giá trị nào "nóng". Đây vừa là chọn feature, vừa là câu trả lời "họ là ai" cho Task 2.

**💻 Code gợi ý:**
```python
def lift_table(col):
    t = df.groupby(col)[TARGET].agg(["count", "mean"])
    t["lift"] = t["mean"] / df[TARGET].mean()
    return t.sort_values("lift", ascending=False)

print(lift_table("5"))   # Main type
```

**✅ Kết quả mong đợi (col "5" Main type):**

| value | count | rate | lift |
|---|---|---|---|
| 2 (Driven Growers) | 502 | 13.1% | **2.20x** |
| 1 (Successful hedonists) | 552 | 8.7% | 1.45x |
| 4 (Career Loners) | 52 | 0% | 0.00x |
| 5,6,10 | … | ~2% | ~0.3x |

→ Insight Task 2: *Driven Growers* mua gấp 2.2 lần trung bình; *Career Loners* gần như không.

## 3.3 — Cột sản phẩm thưa → phân tích nhị phân "có/không"

**🎯 Học gì:** với feature thưa (89.5% = 0), so sánh `=0` vs `>0` mạnh hơn là theo từng giá trị.

**💻 Code gợi ý:**
```python
owns = (df["47"] > 0).astype(int)        # co dong phi bao hiem oto?
print(df.groupby(owns)[TARGET].mean() / df[TARGET].mean())
```

**✅ Kết quả mong đợi:** `>0` → lift **1.55x**, `=0` → **0.42x**. Sở hữu bảo hiểm liên quan = tín hiệu mạnh.

## 3.4 — Information Value (xếp hạng sức mạnh feature)

**🎯 Học gì:** **WoE** (Weight of Evidence) và **IV** (Information Value) — cách định lượng sức dự báo của 1 biến với target nhị phân.

**❓ Tại sao:** IV cho một con số duy nhất/feature để **xếp hạng** trước khi modeling. (Lưu ý: *biến đổi* WoE thuộc Phase 4; ở EDA ta chỉ dùng IV để xếp hạng.)

- WoE mỗi nhóm = `ln(%non_event / %event)`.
- IV = `Σ (%non_event − %event) × WoE`.
- Ngưỡng đọc IV: <0.02 vô dụng · 0.02–0.1 yếu · 0.1–0.3 trung bình · 0.3–0.5 mạnh · >0.5 *nghi ngờ leakage*.

**💻 Code gợi ý:**
```python
def iv(col, eps=0.5):
    t = df.groupby(col)[TARGET].agg(["count", "sum"])
    t["event"]     = t["sum"] + eps                 # +eps tranh chia 0
    t["non_event"] = t["count"] - t["sum"] + eps
    t["p_e"]  = t["event"]     / t["event"].sum()
    t["p_ne"] = t["non_event"] / t["non_event"].sum()
    t["woe"]  = np.log(t["p_ne"] / t["p_e"])
    return ((t["p_ne"] - t["p_e"]) * t["woe"]).sum()

iv_rank = pd.Series({c: iv(c) for c in FEATURES}).sort_values(ascending=False)
print(iv_rank.head(15))
```

**👀 Cần quan sát:** top IV thường rơi vào nhóm bảo hiểm ô tô (44/47/68), purchasing power (43), contribution life/PWAPART… Nếu thấy IV nào >0.5 hãy nghi ngờ và kiểm tra.

## 3.5 — Tương quan & dư thừa

**🎯 Học gì:** phát hiện cặp feature dư thừa (đa cộng tuyến) để cắt ở Phase 4.

**💻 Code gợi ý:**
```python
corr = df[FEATURES].corr()
# vi du cap du thua dien hinh:
print(corr.loc["47", "68"])   # contrib car vs number car

# tim moi cap |corr| > 0.8
high = (corr.abs() > 0.8) & (corr.abs() < 1.0)
pairs = [(a, b) for a in high.index for b in high.columns if a < b and high.loc[a, b]]
print(pairs)
```

**✅ Kết quả mong đợi:** `corr(47,68) ≈ 0.916`. Các cặp contribution↔number (44–64 ↔ 65–85) đều tương quan cao → giữ 1 trong 2. Col 1 ↔ col 5 lồng nhau.

## 3.6 — Phác thảo "chân dung người mua" (cho Task 2)

**🔧 Làm gì:** gom các feature lift cao nhất thành một bức tranh: *người mua MANU thường thuộc Main type 1–2, có sở hữu bảo hiểm ô tô, purchasing power cao…* — diễn đạt dễ hiểu, hành động được cho manager.

**✅ Kết quả mong đợi Phase 3:** (a) bảng lift + IV cho các feature mạnh, (b) danh sách cặp dư thừa cần cắt, (c) bản nháp chân dung khách hàng.

---

# Bài tập tự làm (kiểm tra hiểu)

1. Viết hàm `precision_at_k` rồi kiểm tra: nếu chọn **ngẫu nhiên** 20% người, precision phải ≈ base rate (6%) và lift ≈ 1.0. Vì sao?
2. Tính lift cho cột **43 (Purchasing power)** và **44 (Contribution private third party)**. Giá trị nào "nóng" nhất?
3. Đếm xem trong 85 feature có bao nhiêu cột `near_const` (>99% một giá trị). Nếu bỏ hết chúng thì còn lại bao nhiêu feature?
4. Giải thích bằng lời: tại sao tính IV trên **toàn bộ** data rồi mới chia train/validation lại là **leakage**?

> Làm xong khối này, ta sang Phase 4 (Feature engineering: WoE/encoding/cắt dư thừa) → 9.
