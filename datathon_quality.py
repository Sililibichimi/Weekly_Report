"""Reusable helpers for datathon data quality notebooks.

This module is generated from the original notebook helper cells so the
notebook can focus on displaying results.
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_DIR = Path("datathon")


def csv_row_count(path: Path) -> int:
    """Count rows excluding header. Empty files return 0."""
    if path.stat().st_size == 0:
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return max(sum(1 for _ in f) - 1, 0)


def read_head(path: Path, nrows: int = 5) -> pd.DataFrame:
    if path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, nrows=nrows)


def build_file_inventory(files: list[Path], table_info: dict) -> pd.DataFrame:
    records = []
    for path in files:
        table = path.stem
        head = read_head(path)
        info = table_info.get(table, {})
        records.append(
            {
                "table": table,
                "file": path.name,
                "rows": csv_row_count(path),
                "columns": len(head.columns),
                "layer": info.get("layer", "Unknown"),
                "grain": info.get("grain", "Unknown"),
                "primary_key": ", ".join(info.get("primary_key", [])) or "(composite/none)",
                "business_use": info.get("business_use", ""),
            }
        )
    return pd.DataFrame(records)



# --- From notebook cell 2 ---

TABLE_INFO = {
    "products": {
        "layer": "Master",
        "grain": "1 row per product",
        "primary_key": ["product_id"],
        "business_use": "Product attributes, retail price, product-level COGS.",
    },
    "customers": {
        "layer": "Master",
        "grain": "1 row per customer",
        "primary_key": ["customer_id"],
        "business_use": "Customer profile, signup location, acquisition channel.",
    },
    "promotions": {
        "layer": "Master",
        "grain": "1 row per promotion campaign",
        "primary_key": ["promo_id"],
        "business_use": "Discount type, timing, channel, stackability.",
    },
    "geography": {
        "layer": "Master",
        "grain": "1 row per zip code",
        "primary_key": ["zip"],
        "business_use": "City, region, district mapping.",
    },
    "orders": {
        "layer": "Transaction",
        "grain": "1 row per order",
        "primary_key": ["order_id"],
        "business_use": "Order date, status, customer, source, device, payment method.",
    },
    "order_items": {
        "layer": "Transaction",
        "grain": "1 row per product line inside an order",
        "primary_key": [],
        "business_use": "Quantity, unit price, discount, product and promo usage.",
    },
    "payments": {
        "layer": "Transaction",
        "grain": "1 row per order payment",
        "primary_key": ["order_id"],
        "business_use": "Paid value, installments, payment method.",
    },
    "shipments": {
        "layer": "Transaction",
        "grain": "0 or 1 shipment row per shipped/delivered/returned order",
        "primary_key": ["order_id"],
        "business_use": "Shipping fee and delivery speed.",
    },
    "returns": {
        "layer": "Transaction",
        "grain": "0 or many return rows per order/product",
        "primary_key": ["return_id"],
        "business_use": "Return quantity, refund, return reason.",
    },
    "reviews": {
        "layer": "Transaction",
        "grain": "0 or many review rows per order/product/customer",
        "primary_key": ["review_id"],
        "business_use": "Rating and customer feedback after delivery.",
    },
    "sales": {
        "layer": "Analytical",
        "grain": "1 row per date",
        "primary_key": ["Date"],
        "business_use": "Daily Revenue and COGS for training/analysis.",
    },
    "sample_submission": {
        "layer": "Analytical",
        "grain": "1 row per future date",
        "primary_key": ["Date"],
        "business_use": "Required submission format for forecast horizon.",
    },
    "test": {
        "layer": "Analytical",
        "grain": "Empty CSV in this package; no observable row-level grain",
        "primary_key": [],
        "business_use": "Empty test file; ignore for current overview unless populated later.",
    },
    "inventory": {
        "layer": "Operational",
        "grain": "1 row per product per month snapshot",
        "primary_key": [],
        "business_use": "Stockout, overstock, fill rate, sell-through.",
    },
    "web_traffic": {
        "layer": "Operational",
        "grain": "1 row per date and traffic source",
        "primary_key": [],
        "business_use": "Sessions, visitors, page views, bounce rate.",
    },
}

RELATIONSHIPS = [
    ("orders", "customer_id", "customers", "customer_id", "many-to-one"),
    ("orders", "zip", "geography", "zip", "many-to-one"),
    ("order_items", "order_id", "orders", "order_id", "many-to-one"),
    ("order_items", "product_id", "products", "product_id", "many-to-one"),
    ("order_items", "promo_id", "promotions", "promo_id", "many-to-zero-or-one"),
    ("order_items", "promo_id_2", "promotions", "promo_id", "many-to-zero-or-one"),
    ("payments", "order_id", "orders", "order_id", "one-to-one"),
    ("shipments", "order_id", "orders", "order_id", "zero-or-one-to-one"),
    ("returns", "order_id", "orders", "order_id", "many-to-one"),
    ("returns", "product_id", "products", "product_id", "many-to-one"),
    ("reviews", "order_id", "orders", "order_id", "many-to-one"),
    ("reviews", "product_id", "products", "product_id", "many-to-one"),
    ("reviews", "customer_id", "customers", "customer_id", "many-to-one"),
    ("inventory", "product_id", "products", "product_id", "many-to-one"),
]


# --- From notebook cell 6 ---

import matplotlib.dates as mdates

try:
    from IPython.display import display as notebook_display
except ImportError:
    notebook_display = None


LAYER_ORDER = ["Master", "Transaction", "Analytical", "Operational", "Unknown"]

LAYER_COLORS = {
    "Master": "#4E79A7",
    "Transaction": "#59A14F",
    "Analytical": "#F28E2B",
    "Operational": "#E15759",
    "Unknown": "#9D9D9D",
}

DATE_COLUMN_HINTS = {
    "customers": ["signup_date"],
    "promotions": ["start_date", "end_date"],
    "orders": ["order_date"],
    "shipments": ["ship_date", "delivery_date"],
    "returns": ["return_date"],
    "reviews": ["review_date"],
    "sales": ["Date"],
    "sample_submission": ["Date"],
    "inventory": ["snapshot_date"],
    "web_traffic": ["date"],
}

DIRECT_REVENUE_PROFIT = {
    "sales": "Yes - already daily Revenue and COGS",
    "order_items": "Yes - line revenue; join products for COGS/profit",
    "payments": "Revenue cash view only; no COGS",
    "returns": "Refund impact only; aggregate before net revenue",
    "products": "COGS/price lookup only",
}

AGGREGATE_BEFORE_JOIN = {
    "order_items": "Usually yes if joining to order-level/payment/shipment tables",
    "returns": "Yes - aggregate by order_id/product_id or order_id",
    "reviews": "Yes - aggregate by order_id/product_id/customer_id",
    "inventory": "Yes - aggregate by product_id/date period",
    "web_traffic": "Yes - aggregate by date/source or date",
    "promotions": "No for promo lookup; many rows can match only if joining by date range",
}

MAIN_USAGE = {
    "customers": "Master data for customer segmentation and acquisition analysis.",
    "geography": "Master data for region/district enrichment.",
    "products": "Master data for product attributes, price, and COGS lookup.",
    "promotions": "Master data for campaign, discount, and promo eligibility context.",
    "orders": "Transaction header for order date, customer, channel, status, device.",
    "order_items": "Transaction line table for quantity, price, discount, revenue analysis.",
    "payments": "Transaction payment view for paid value and installment behavior.",
    "shipments": "Transaction logistics view for shipping fee and delivery speed.",
    "returns": "Transaction return/refund view; use to adjust net revenue and quality issues.",
    "reviews": "Transaction feedback view for ratings and post-purchase signals.",
    "sales": "Analytical daily Revenue/COGS table; can be used directly for revenue/profit.",
    "sample_submission": "Analytical forecast submission template for future dates.",
    "test": "Empty analytical file in this package; not usable until populated.",
    "inventory": "Operational monthly stock snapshot; aggregate before sales joins.",
    "web_traffic": "Operational traffic by date/source; aggregate before date-level joins.",
}


# --- From notebook cell 7 ---

def display_table(df: pd.DataFrame, caption: str, formatters: dict | None = None) -> None:
    """Show a compact styled dataframe in notebooks; print plain text elsewhere."""
    if notebook_display is None:
        print(caption)
        print(df.to_string(index=False))
        return

    styled = df.style.set_caption(caption)
    if formatters:
        styled = styled.format(formatters)
    notebook_display(styled)


def get_date_meta(path: Path) -> dict:
    """Return the primary date columns and overall date range for one CSV."""
    empty_result = {
        "date_column": "",
        "date_range": "",
        "min_date": pd.NaT,
        "max_date": pd.NaT,
    }
    if path.stat().st_size == 0:
        return empty_result

    table_name = path.stem
    columns = pd.read_csv(path, nrows=0).columns.tolist()
    hinted_columns = [col for col in DATE_COLUMN_HINTS.get(table_name, []) if col in columns]
    detected_columns = [col for col in columns if "date" in col.lower()]
    date_columns = hinted_columns or detected_columns

    if not date_columns:
        return empty_result

    date_df = pd.read_csv(path, usecols=date_columns, low_memory=False)
    valid_ranges = []
    for column in date_columns:
        parsed = pd.to_datetime(date_df[column], errors="coerce")
        if parsed.notna().any():
            valid_ranges.append((parsed.min(), parsed.max()))

    if not valid_ranges:
        return {
            **empty_result,
            "date_column": ", ".join(date_columns),
            "date_range": "No valid dates",
        }

    min_date = min(item[0] for item in valid_ranges)
    max_date = max(item[1] for item in valid_ranges)
    return {
        "date_column": ", ".join(date_columns),
        "date_range": f"{min_date:%Y-%m-%d} to {max_date:%Y-%m-%d}",
        "min_date": min_date,
        "max_date": max_date,
    }


def build_date_meta(files: list[Path]) -> pd.DataFrame:
    records = [{"table": path.stem, **get_date_meta(path)} for path in files]
    return pd.DataFrame(records)


def build_table_overview(
    inventory_df: pd.DataFrame,
    date_meta: pd.DataFrame,
) -> pd.DataFrame:
    overview = (
        inventory_df.merge(date_meta, on="table", how="left")
        .assign(
            main_usage=lambda df: df["table"].map(MAIN_USAGE).fillna(df["business_use"]),
            primary_key=lambda df: df["primary_key"].replace({"(composite/none)": ""}),
        )
        .rename(columns={"table": "table_name"})
    )
    columns = [
        "table_name",
        "rows",
        "columns",
        "grain",
        "primary_key",
        "date_column",
        "date_range",
        "main_usage",
    ]
    return overview[columns].sort_values("table_name").reset_index(drop=True)


def build_decision_matrix(inventory_df: pd.DataFrame) -> pd.DataFrame:
    return (
        inventory_df[["table", "layer"]]
        .rename(columns={"table": "table_name", "layer": "data_type"})
        .assign(
            direct_revenue_profit=lambda df: df["table_name"]
            .map(DIRECT_REVENUE_PROFIT)
            .fillna("No - enrichment or operational context"),
            aggregate_before_join=lambda df: df["table_name"]
            .map(AGGREGATE_BEFORE_JOIN)
            .fillna("No - can usually join at its declared grain"),
        )
        .sort_values(["data_type", "table_name"])
        .reset_index(drop=True)
    )


def build_plot_df(inventory_df: pd.DataFrame, date_meta: pd.DataFrame) -> pd.DataFrame:
    return (
        inventory_df.merge(date_meta[["table", "min_date", "max_date"]], on="table", how="left")
        .rename(columns={"table": "table_name"})
        .assign(rows_for_plot=lambda df: df["rows"].clip(lower=1))
    )


def layer_colors(values: pd.Series) -> list[str]:
    return [LAYER_COLORS.get(value, LAYER_COLORS["Unknown"]) for value in values]


def clean_axis(ax, title: str, xlabel: str | None = None, ylabel: str | None = None) -> None:
    ax.set_title(title, fontsize=12, pad=12)
    ax.set_xlabel(xlabel or "")
    ax.set_ylabel(ylabel or "")
    ax.grid(axis="x", alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)


def plot_table_type_counts(data: pd.DataFrame):
    counts = data["layer"].value_counts().reindex(LAYER_ORDER).dropna()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(counts.index, counts.values, color=layer_colors(counts.index.to_series()))
    clean_axis(ax, "Tables by data type", ylabel="tables")
    ax.tick_params(axis="x", rotation=15)
    plt.tight_layout()

def plot_rows_by_table(data: pd.DataFrame):
    sorted_data = data.sort_values("rows", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(
        sorted_data["table_name"],
        sorted_data["rows_for_plot"],
        color=layer_colors(sorted_data["layer"]),
    )
    ax.set_xscale("log")
    clean_axis(ax, "Rows by table", xlabel="rows, log scale")
    for index, row in enumerate(sorted_data.itertuples()):
        ax.text(row.rows_for_plot * 1.08, index, f"{row.rows:,}", va="center", fontsize=8)
    plt.tight_layout()


def plot_rows_vs_columns(data: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(
        data["columns"],
        data["rows_for_plot"],
        s=100,
        c=layer_colors(data["layer"]),
        edgecolor="white",
        linewidth=0.8,
    )
    ax.set_yscale("log")
    clean_axis(ax, "Rows vs columns", xlabel="columns", ylabel="rows, log scale")
    for row in data.itertuples():
        ax.annotate(
            row.table_name,
            (row.columns, row.rows_for_plot),
            fontsize=8,
            textcoords="offset points",
            xytext=(5, 3),
        )
    plt.tight_layout()


def plot_date_coverage(data: pd.DataFrame):
    timeline = data.dropna(subset=["min_date", "max_date"]).sort_values("min_date")
    fig, ax = plt.subplots(figsize=(10, 5))
    if timeline.empty:
        ax.text(0.5, 0.5, "No date columns detected", ha="center", va="center")
        ax.axis("off")
        return fig

    left = timeline["min_date"].map(mdates.date2num)
    widths = (timeline["max_date"] - timeline["min_date"]).dt.days.clip(lower=1)
    ax.barh(
        timeline["table_name"],
        widths,
        left=left,
        color=layer_colors(timeline["layer"]),
    )
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=30)
    clean_axis(ax, "Date coverage by table", xlabel="calendar period")
    plt.tight_layout()


def plot_join_preparation(decision_matrix: pd.DataFrame):
    prep = decision_matrix.assign(
        join_preparation=lambda df: df["aggregate_before_join"].str.startswith(("Yes", "Usually"))
    )
    prep_counts = (
        prep["join_preparation"]
        .map({True: "Aggregate first", False: "Direct join ok"})
        .value_counts()
        .reindex(["Direct join ok", "Aggregate first"])
        .fillna(0)
    )

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.barh(prep_counts.index, prep_counts.values, color=["#4E79A7", "#E15759"])
    clean_axis(ax, "Join preparation needed", xlabel="tables")
    for index, value in enumerate(prep_counts.values):
        ax.text(value + 0.1, index, int(value), va="center")
    plt.tight_layout()


# --- From notebook cell 16 ---

SEMANTIC_OVERRIDES = {
    "Date": "date",
    "date": "date",
    "order_date": "date",
    "signup_date": "date",
    "ship_date": "date",
    "delivery_date": "date",
    "return_date": "date",
    "review_date": "date",
    "snapshot_date": "date",
    "start_date": "date",
    "end_date": "date",
    "customer_id": "id",
    "product_id": "id",
    "promo_id": "id",
    "promo_id_2": "id",
    "order_id": "id",
    "return_id": "id",
    "review_id": "id",
    "zip": "id",
    "price": "numeric_continuous",
    "cogs": "numeric_continuous",
    "Revenue": "numeric_continuous",
    "COGS": "numeric_continuous",
    "payment_value": "numeric_continuous",
    "shipping_fee": "numeric_continuous",
    "refund_amount": "numeric_continuous",
    "unit_price": "numeric_continuous",
    "discount_amount": "numeric_continuous",
    "sessions": "numeric_continuous",
    "unique_visitors": "numeric_continuous",
    "page_views": "numeric_continuous",
    "bounce_rate": "numeric_continuous",
    "avg_session_duration_sec": "numeric_continuous",
    "fill_rate": "numeric_continuous",
    "sell_through_rate": "numeric_continuous",
    "stock_on_hand": "numeric_discrete",
    "units_received": "numeric_discrete",
    "units_sold": "numeric_discrete",
    "quantity": "numeric_discrete",
    "installments": "numeric_discrete",
    "rating": "numeric_discrete",
    "stockout_days": "numeric_discrete",
    "days_of_supply": "numeric_discrete",
    "year": "numeric_discrete",
    "month": "numeric_discrete",
    "stockout_flag": "boolean_flag",
    "overstock_flag": "boolean_flag",
    "reorder_flag": "boolean_flag",
    "stackable_flag": "boolean_flag",
    "review_title": "text",
    "product_name": "categorical_high_cardinality",
    "promo_name": "categorical_high_cardinality",
    "city": "categorical_high_cardinality",
    "district": "categorical_high_cardinality",
    "gender": "categorical_low_cardinality",
    "age_group": "categorical_low_cardinality",
    "acquisition_channel": "categorical_low_cardinality",
    "order_status": "categorical_low_cardinality",
    "payment_method": "categorical_low_cardinality",
    "device_type": "categorical_low_cardinality",
    "order_source": "categorical_low_cardinality",
    "category": "categorical_low_cardinality",
    "segment": "categorical_low_cardinality",
    "promo_type": "categorical_low_cardinality",
    "promo_channel": "categorical_low_cardinality",
    "applicable_category": "categorical_low_cardinality",
    "return_reason": "categorical_low_cardinality",
    "traffic_source": "categorical_low_cardinality",
    "size": "categorical_low_cardinality",
    "color": "categorical_low_cardinality",
    "region": "categorical_low_cardinality",
}

BOOLEAN_ALLOWED_VALUES = {0, 1, True, False, "0", "1", "true", "false", "True", "False", "yes", "no", "Yes", "No"}
CATEGORY_DETAIL_THRESHOLD = 30

CORE_REVENUE_TABLES = ["sales", "orders", "order_items", "products", "payments"]
SAMPLE_VALUE_LIMIT = 3
SAMPLE_VALUE_MAX_CHARS = 45


# --- From notebook cell 17 ---

def read_csv_for_profile(path: Path) -> pd.DataFrame:
    if path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def shorten_text(value: str, max_chars: int = SAMPLE_VALUE_MAX_CHARS) -> str:
    text = str(value)
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def compact_sample_values(
    series: pd.Series,
    max_values: int = SAMPLE_VALUE_LIMIT,
    max_chars: int = SAMPLE_VALUE_MAX_CHARS,
) -> str:
    values = series.dropna().astype(str).unique()[:max_values]
    return " | ".join(shorten_text(value, max_chars) for value in values)


def infer_semantic_type(table_name: str, column: str, series: pd.Series) -> str:
    if column in SEMANTIC_OVERRIDES:
        return SEMANTIC_OVERRIDES[column]

    column_lower = column.lower()
    unique_count = series.nunique(dropna=True)
    unique_pct = unique_count / max(series.notna().sum(), 1) * 100

    if "date" in column_lower:
        return "date"
    if column_lower.endswith("_id") or column_lower == "id":
        return "id"
    if "flag" in column_lower or series.dropna().isin([0, 1, True, False]).all():
        return "boolean_flag"
    if pd.api.types.is_numeric_dtype(series):
        if pd.api.types.is_integer_dtype(series) and unique_count <= 30:
            return "numeric_discrete"
        return "numeric_continuous"
    if "title" in column_lower or "comment" in column_lower or "description" in column_lower:
        return "text"
    if unique_count <= CATEGORY_DETAIL_THRESHOLD and unique_pct < 80:
        return "categorical_low_cardinality"
    return "categorical_high_cardinality"


def profile_column(table_name: str, column: str, series: pd.Series, row_count: int) -> dict:
    non_null_count = int(series.notna().sum())
    unique_count = int(series.nunique(dropna=True))
    semantic_type = infer_semantic_type(table_name, column, series)
    return {
        "table_name": table_name,
        "column_name": column,
        "semantic_type": semantic_type,
        "pandas_dtype": str(series.dtype),
        "unique_count": unique_count,
        "unique_pct": round(unique_count / max(non_null_count, 1) * 100, 2),
        "sample_values": compact_sample_values(series),
    }


def build_column_profile_summary(files: list[Path]) -> pd.DataFrame:
    records = []
    for path in files:
        table_name = path.stem
        df = read_csv_for_profile(path)
        row_count = len(df)
        for column in df.columns:
            records.append(profile_column(table_name, column, df[column], row_count))
    return pd.DataFrame(records)


def build_table_type_summary(column_profile: pd.DataFrame) -> pd.DataFrame:
    type_groups = {
        "id_cols": ["id"],
        "numeric_cols": ["numeric_continuous", "numeric_discrete"],
        "categorical_cols": ["categorical_low_cardinality", "categorical_high_cardinality"],
        "boolean_cols": ["boolean_flag"],
        "date_cols": ["date"],
        "text_cols": ["text"],
    }
    records = []
    for table_name, group in column_profile.groupby("table_name"):
        record = {"table_name": table_name}
        for output_column, semantic_types in type_groups.items():
            record[output_column] = int(group["semantic_type"].isin(semantic_types).sum())
        records.append(record)
    return pd.DataFrame(records).sort_values("table_name").reset_index(drop=True)


def normalized_string_groups(series: pd.Series) -> list[str]:
    text = series.dropna().astype(str)
    if text.empty:
        return []
    normalized = text.str.strip().str.lower()
    groups = {}
    for original, key in zip(text, normalized):
        groups.setdefault(key, set()).add(original)
    suspicious = [sorted(values) for values in groups.values() if len(values) > 1]
    return [str(values) for values in suspicious[:5]]


def value_counts_summary(series: pd.Series, max_values: int = 30) -> str:
    counts = series.fillna("(missing)").astype(str).value_counts(dropna=False).head(max_values)
    pct = series.fillna("(missing)").astype(str).value_counts(normalize=True, dropna=False).head(max_values) * 100
    return str({key: {"count": int(counts[key]), "pct": round(float(pct[key]), 2)} for key in counts.index})


def values_or_top_values(series: pd.Series, unique_count: int) -> str:
    clean = series.dropna().astype(str)
    if unique_count <= CATEGORY_DETAIL_THRESHOLD:
        return str(sorted(clean.unique().tolist()))
    return str(clean.value_counts().head(10).index.tolist())


def suspicious_category_values(series: pd.Series, semantic_type: str) -> str:
    issues = []
    if semantic_type == "boolean_flag":
        invalid = sorted(set(series.dropna()) - BOOLEAN_ALLOWED_VALUES)
        if invalid:
            issues.append(f"invalid boolean values: {invalid[:10]}")
    string_issues = normalized_string_groups(series)
    if string_issues:
        issues.append(f"case/space variants: {string_issues}")
    return " | ".join(issues)


def build_category_domain_summary(column_profile: pd.DataFrame, files: list[Path]) -> pd.DataFrame:
    profile_lookup = {
        (row.table_name, row.column_name): row
        for row in column_profile.itertuples(index=False)
    }
    records = []
    semantic_types = {
        "categorical_low_cardinality",
        "categorical_high_cardinality",
        "boolean_flag",
    }
    for path in files:
        table_name = path.stem
        df = read_csv_for_profile(path)
        for column in df.columns:
            profile = profile_lookup.get((table_name, column))
            if profile is None or profile.semantic_type not in semantic_types:
                continue
            suspicious = suspicious_category_values(df[column], profile.semantic_type)
            records.append(
                {
                    "table_name": table_name,
                    "column_name": column,
                    "unique_count": int(profile.unique_count),
                    "values_or_top_values": values_or_top_values(df[column], int(profile.unique_count)),
                    "value_counts": value_counts_summary(df[column]),
                    "suspicious_values": suspicious,
                    "note": "Review suspicious values." if suspicious else "Domain looks consistent.",
                }
            )
    return pd.DataFrame(records).sort_values(["table_name", "column_name"]).reset_index(drop=True)


# --- From notebook cell 18 ---

def numeric_stats_for_column(table_name: str, column: str, series: pd.Series) -> dict:
    numeric = pd.to_numeric(series, errors="coerce")
    clean = numeric.dropna()
    if clean.empty:
        return {
            "table_name": table_name,
            "column_name": column,
            "min": pd.NA,
            "p1": pd.NA,
            "median": pd.NA,
            "mean": pd.NA,
            "p99": pd.NA,
            "max": pd.NA,
            "negative_count": 0,
        }
    return {
        "table_name": table_name,
        "column_name": column,
        "min": clean.min(),
        "p1": clean.quantile(0.01),
        "median": clean.median(),
        "mean": clean.mean(),
        "p99": clean.quantile(0.99),
        "max": clean.max(),
        "negative_count": int((clean < 0).sum()),
    }


def build_numeric_profile_summary(column_profile: pd.DataFrame, files: list[Path]) -> pd.DataFrame:
    numeric_types = {"numeric_continuous", "numeric_discrete"}
    records = []
    for path in files:
        table_name = path.stem
        df = read_csv_for_profile(path)
        numeric_columns = column_profile.query(
            "table_name == @table_name and semantic_type in @numeric_types"
        )["column_name"].tolist()
        for column in numeric_columns:
            records.append(numeric_stats_for_column(table_name, column, df[column]))
    return pd.DataFrame(records)


def date_stats_for_column(table_name: str, column: str, series: pd.Series) -> dict:
    parsed = pd.to_datetime(series, errors="coerce")
    invalid_count = int(parsed.isna().sum() - series.isna().sum())
    return {
        "table_name": table_name,
        "column_name": column,
        "min_date": parsed.min(),
        "max_date": parsed.max(),
        "invalid_date_count": invalid_count,
        "parse_success_pct": round(parsed.notna().sum() / max(series.notna().sum(), 1) * 100, 2),
    }


def build_date_parse_summary(column_profile: pd.DataFrame, files: list[Path]) -> pd.DataFrame:
    records = []
    for path in files:
        table_name = path.stem
        df = read_csv_for_profile(path)
        date_columns = column_profile.query(
            "table_name == @table_name and semantic_type == 'date'"
        )["column_name"].tolist()
        for column in date_columns:
            records.append(date_stats_for_column(table_name, column, df[column]))
    return pd.DataFrame(records)


def expected_dtype_for_semantic_type(semantic_type: str) -> str:
    if semantic_type in {"numeric_continuous", "numeric_discrete"}:
        return "numeric"
    if semantic_type == "boolean_flag":
        return "boolean-like"
    if semantic_type == "date":
        return "datetime-parseable"
    if semantic_type == "id":
        return "id/string-or-integer"
    if semantic_type == "text":
        return "text"
    return "categorical"


def dtype_issue_for_column(table_name: str, column: str, series: pd.Series, semantic_type: str) -> dict | None:
    actual_type = str(series.dtype)
    expected_type = expected_dtype_for_semantic_type(semantic_type)

    if semantic_type in {"numeric_continuous", "numeric_discrete"}:
        numeric = pd.to_numeric(series, errors="coerce")
        if not pd.api.types.is_numeric_dtype(series) and numeric.notna().sum() > 0:
            return {
                "table_name": table_name,
                "column_name": column,
                "expected_type": expected_type,
                "actual_type": actual_type,
                "issue": "Numeric semantic column is stored as non-numeric dtype.",
                "severity": "Medium",
                "decision": "Convert with pd.to_numeric before numeric checks.",
            }

    if semantic_type == "date":
        parsed = pd.to_datetime(series, errors="coerce")
        invalid_count = int(parsed.isna().sum() - series.isna().sum())
        if invalid_count > 0:
            return {
                "table_name": table_name,
                "column_name": column,
                "expected_type": expected_type,
                "actual_type": actual_type,
                "issue": f"{invalid_count} non-null values cannot be parsed as datetime.",
                "severity": "High",
                "decision": "Investigate source date format before time analysis.",
            }

    if semantic_type == "boolean_flag":
        invalid = sorted(set(series.dropna()) - BOOLEAN_ALLOWED_VALUES)
        if invalid:
            return {
                "table_name": table_name,
                "column_name": column,
                "expected_type": expected_type,
                "actual_type": actual_type,
                "issue": f"Boolean flag has invalid values: {invalid[:10]}",
                "severity": "High",
                "decision": "Fix or map invalid boolean values.",
            }

    suspicious = suspicious_category_values(series, semantic_type)
    if semantic_type.startswith("categorical") and suspicious:
        return {
            "table_name": table_name,
            "column_name": column,
            "expected_type": expected_type,
            "actual_type": actual_type,
            "issue": suspicious,
            "severity": "Low",
            "decision": "Standardize labels if used for grouping/modeling.",
        }

    return None


def build_dtype_issues(column_profile: pd.DataFrame, files: list[Path]) -> pd.DataFrame:
    records = []
    profile_lookup = {
        (row.table_name, row.column_name): row.semantic_type
        for row in column_profile.itertuples(index=False)
    }
    for path in files:
        table_name = path.stem
        df = read_csv_for_profile(path)
        for column in df.columns:
            semantic_type = profile_lookup[(table_name, column)]
            issue = dtype_issue_for_column(table_name, column, df[column], semantic_type)
            if issue:
                records.append(issue)
    columns = ["table_name", "column_name", "expected_type", "actual_type", "issue", "severity", "decision"]
    return pd.DataFrame(records, columns=columns)




SEMANTIC_TYPE_ORDER = [
    "id",
    "date",
    "numeric_continuous",
    "numeric_discrete",
    "boolean_flag",
    "categorical_low_cardinality",
    "categorical_high_cardinality",
    "text",
]

SEMANTIC_TYPE_COLORS = {
    "id": "#4E79A7",
    "date": "#76B7B2",
    "numeric_continuous": "#59A14F",
    "numeric_discrete": "#8CD17D",
    "boolean_flag": "#B07AA1",
    "categorical_low_cardinality": "#F28E2B",
    "categorical_high_cardinality": "#FFBE7D",
    "text": "#9D9D9D",
}


def table_grain_and_usage(table_name: str) -> str:
    info = TABLE_INFO.get(table_name, {})
    grain = info.get("grain", "")
    usage = info.get("business_use", "")
    return f"{grain}. {usage}".strip()


def core_table_profile(table_name: str, column_profile: pd.DataFrame) -> pd.DataFrame:
    return (
        column_profile.query("table_name == @table_name")
        .copy()
        .reset_index(drop=True)
    )


def low_cardinality_columns(table_name: str, column_profile: pd.DataFrame, max_columns: int = 4) -> list[str]:
    profile = core_table_profile(table_name, column_profile)
    domain_types = {"categorical_low_cardinality", "boolean_flag"}
    return (
        profile.query("semantic_type in @domain_types and unique_count <= @CATEGORY_DETAIL_THRESHOLD")
        .sort_values(["unique_count", "column_name"])
        ["column_name"]
        .head(max_columns)
        .tolist()
    )


def plot_column_cards(ax, profile: pd.DataFrame, table_name: str) -> None:
    y_positions = list(range(len(profile)))
    colors = [SEMANTIC_TYPE_COLORS.get(value, "#9D9D9D") for value in profile["semantic_type"]]
    ax.barh(y_positions, [1] * len(profile), color=colors, height=0.82, alpha=0.95)

    for idx, row in enumerate(profile.itertuples(index=False)):
        title = (
            f"{row.column_name}  |  {row.semantic_type}  |  {row.pandas_dtype}  |  "
            f"unique {row.unique_count:,} ({row.unique_pct:.1f}%)"
        )
        ax.text(0.02, idx - 0.13, title, va="center", ha="left", fontsize=10.5, color="#111111")
        ax.text(0.02, idx + 0.18, f"sample: {row.sample_values}", va="center", ha="left", fontsize=9, color="#333333")

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.7, len(profile) - 0.3)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"{table_name} - {len(profile)} columns", loc="left", fontsize=13, pad=10)
    ax.spines[["top", "right", "bottom", "left"]].set_visible(False)


def plot_domain_bars(ax, table_name: str, column_name: str) -> None:
    df = read_csv_for_profile(DATA_DIR / f"{table_name}.csv")
    counts = df[column_name].fillna("(missing)").astype(str).value_counts().head(8)
    counts = counts.sort_values()
    ax.barh(counts.index, counts.values, color="#4E79A7", alpha=0.85)
    ax.set_title(column_name, fontsize=10, loc="left", pad=6)
    ax.tick_params(axis="both", labelsize=8)
    ax.grid(axis="x", alpha=0.2)
    ax.spines[["top", "right", "left"]].set_visible(False)


def plot_core_table_profile(table_name: str, column_profile: pd.DataFrame):
    profile = core_table_profile(table_name, column_profile)
    domain_columns = low_cardinality_columns(table_name, column_profile)
    domain_rows = max(len(domain_columns), 1)
    fig_height = max(5.2, len(profile) * 0.78)
    fig = plt.figure(figsize=(16, fig_height))
    grid = fig.add_gridspec(domain_rows, 2, width_ratios=[2.25, 1], wspace=0.3, hspace=0.55)

    ax_profile = fig.add_subplot(grid[:, 0])
    plot_column_cards(ax_profile, profile, table_name)

    if domain_columns:
        for row_idx, column_name in enumerate(domain_columns):
            ax_domain = fig.add_subplot(grid[row_idx, 1])
            plot_domain_bars(ax_domain, table_name, column_name)
    else:
        ax_empty = fig.add_subplot(grid[:, 1])
        ax_empty.text(0.5, 0.5, "No low-cardinality categorical/boolean columns", ha="center", va="center", fontsize=10)
        ax_empty.axis("off")

    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color=SEMANTIC_TYPE_COLORS[item], label=item)
        for item in SEMANTIC_TYPE_ORDER
        if item in set(profile["semantic_type"])
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=4, frameon=False, fontsize=8)
    fig.suptitle(table_grain_and_usage(table_name), fontsize=10, y=0.985)
    fig.subplots_adjust(left=0.03, right=0.98, top=0.90, bottom=0.12, wspace=0.30, hspace=0.65)


def plot_appendix_schema_overview(column_profile: pd.DataFrame):
    appendix_tables = [table for table in sorted(column_profile["table_name"].unique()) if table not in CORE_REVENUE_TABLES]
    data = (
        column_profile.query("table_name in @appendix_tables")
        .groupby(["table_name", "semantic_type"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=SEMANTIC_TYPE_ORDER, fill_value=0)
    )

    fig, ax = plt.subplots(figsize=(12, max(4, len(data) * 0.45)))
    left = [0] * len(data)
    y = range(len(data))
    for semantic_type in SEMANTIC_TYPE_ORDER:
        values = data[semantic_type].values
        if values.sum() == 0:
            continue
        ax.barh(
            list(y),
            values,
            left=left,
            label=semantic_type,
            color=SEMANTIC_TYPE_COLORS.get(semantic_type, "#9D9D9D"),
        )
        left = [current + value for current, value in zip(left, values)]

    ax.set_yticks(list(y))
    ax.set_yticklabels(data.index)
    ax.invert_yaxis()
    clean_axis(ax, "Appendix schema overview", xlabel="columns")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.28), ncol=4, frameon=False, fontsize=8)
    plt.tight_layout()



def plot_schema_dtype_issues(dtype_issues: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 2.5))
    if dtype_issues.empty:
        ax.text(0.5, 0.5, "No dtype/domain issues detected", ha="center", va="center", fontsize=12)
        ax.axis("off")
        return fig

    counts = dtype_issues["severity"].value_counts().sort_index()
    ax.bar(counts.index, counts.values, color="#E15759")
    clean_axis(ax, "dtype/domain issues", ylabel="columns")
    for index, value in enumerate(counts.values):
        ax.text(index, value + 0.05, int(value), ha="center")
    plt.tight_layout()


# --- From notebook cell 28 ---

MISSING_RULES = {
    ("order_items", "promo_id"): {
        "interpretation": "Business expected - order line did not use a primary promotion.",
        "action": "Keep as missing or fill with 'NO_PROMO' only for modeling/reporting labels.",
    },
    ("order_items", "promo_id_2"): {
        "interpretation": "Business expected - second stacked promotion is rarely used.",
        "action": "Keep as missing; create a has_second_promo flag if needed.",
    },
    ("promotions", "applicable_category"): {
        "interpretation": "Business expected - promotion appears to apply to all categories.",
        "action": "Treat missing as 'ALL_CATEGORIES' for promo eligibility analysis.",
    },
}

REVENUE_CRITICAL_COLUMNS = {
    ("products", "price"),
    ("products", "cogs"),
    ("order_items", "quantity"),
    ("order_items", "unit_price"),
    ("order_items", "discount_amount"),
    ("orders", "order_id"),
    ("orders", "order_date"),
    ("payments", "payment_value"),
    ("sales", "Revenue"),
    ("sales", "COGS"),
}


# --- From notebook cell 29 ---

def classify_missing(table_name: str, column: str, missing_count: int) -> dict:
    """Attach business interpretation and action to a missing-value finding."""
    if missing_count == 0:
        return {
            "interpretation": "No missing values.",
            "action": "No action needed.",
        }

    rule = MISSING_RULES.get((table_name, column))
    if rule:
        return rule

    if (table_name, column) in REVENUE_CRITICAL_COLUMNS:
        return {
            "interpretation": "Potential data issue - critical for revenue/profit analysis.",
            "action": "Investigate before using this table for revenue/profit metrics.",
        }

    return {
        "interpretation": "Potential data issue or undocumented business meaning.",
        "action": "Investigate source definition; decide whether to fill, keep, or exclude.",
    }


def summarize_missing_for_table(path: Path) -> pd.DataFrame:
    """Return missing-value summary for every column in one CSV."""
    table_name = path.stem
    if path.stat().st_size == 0:
        return pd.DataFrame(
            [
                {
                    "table_name": table_name,
                    "column": "",
                    "missing_count": 0,
                    "missing_pct": 0.0,
                    "interpretation": "Empty file - no columns to inspect.",
                    "action": "Ignore until the file is populated.",
                }
            ]
        )

    df = pd.read_csv(path, low_memory=False)
    row_count = len(df)
    records = []
    for column in df.columns:
        missing_count = int(df[column].isna().sum())
        classification = classify_missing(table_name, column, missing_count)
        records.append(
            {
                "table_name": table_name,
                "column": column,
                "missing_count": missing_count,
                "missing_pct": round(missing_count / max(row_count, 1) * 100, 2),
                **classification,
            }
        )
    return pd.DataFrame(records)


def build_missing_summary(files: list[Path], only_missing: bool = True) -> pd.DataFrame:
    summary = pd.concat(
        [summarize_missing_for_table(path) for path in files],
        ignore_index=True,
    )
    if only_missing:
        summary = summary.query("missing_count > 0").copy()
    return summary.sort_values(
        ["missing_pct", "missing_count", "table_name", "column"],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)


def build_missing_profile(files: list[Path]) -> pd.DataFrame:
    profile = pd.concat(
        [summarize_missing_for_table(path) for path in files],
        ignore_index=True,
    )
    return profile.sort_values(["table_name", "column"]).reset_index(drop=True)


def plot_missing_columns(summary: pd.DataFrame, top_n: int = 15):
    plot_data = summary.head(top_n).sort_values("missing_pct", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 4))
    if plot_data.empty:
        ax.text(0.5, 0.5, "No missing values found", ha="center", va="center")
        ax.axis("off")
        return fig

    labels = plot_data["table_name"] + "." + plot_data["column"]
    ax.barh(labels, plot_data["missing_pct"], color="#E15759")
    clean_axis(ax, "Top missing columns", xlabel="missing %")
    for index, row in enumerate(plot_data.itertuples()):
        ax.text(row.missing_pct + 1, index, f"{row.missing_pct:.2f}%", va="center", fontsize=8)
    plt.tight_layout()


def plot_missing_interpretation(summary: pd.DataFrame):
    plot_data = (
        summary.assign(
            missing_type=lambda df: df["interpretation"].str.split(" - ").str[0]
        )
        .groupby("missing_type", dropna=False)["missing_count"]
        .sum()
        .sort_values()
    )

    fig, ax = plt.subplots(figsize=(8, 3.5))
    if plot_data.empty:
        ax.text(0.5, 0.5, "No missing values found", ha="center", va="center")
        ax.axis("off")
        return fig

    colors = ["#59A14F" if "Business expected" in label else "#E15759" for label in plot_data.index]
    ax.barh(plot_data.index, plot_data.values, color=colors)
    clean_axis(ax, "Missing values by interpretation", xlabel="missing cells")
    for index, value in enumerate(plot_data.values):
        ax.text(value * 1.01, index, f"{int(value):,}", va="center", fontsize=8)
    plt.tight_layout()


# --- From notebook cell 35 ---

DATE_RANGE_CHECKS = {
    "sales": ["Date"],
    "orders": ["order_date"],
    "customers": ["signup_date"],
    "shipments": ["ship_date", "delivery_date"],
    "returns": ["return_date"],
    "reviews": ["review_date"],
    "inventory": ["snapshot_date"],
    "web_traffic": ["date"],
    "promotions": ["start_date", "end_date"],
}

FORECAST_AVAILABILITY = {
    "sales.Date": "Known before forecast as calendar date.",
    "orders.order_date": "Known only after order occurs; use historical lags, not future orders.",
    "customers.signup_date": "Known for existing customers; future signups are not known.",
    "shipments.ship_date": "Known only after fulfillment; leakage for same-day future forecast.",
    "shipments.delivery_date": "Known after delivery; leakage for future forecast.",
    "returns.return_date": "Known after return; leakage for future forecast.",
    "reviews.review_date": "Known after review; leakage for future forecast.",
    "inventory.snapshot_date": "Known only for historical snapshots unless future inventory plan is provided.",
    "web_traffic.date": "Known as calendar date, but traffic metrics are only known after the day.",
    "promotions.start_date": "Can be known before forecast if promotion calendar is planned.",
    "promotions.end_date": "Can be known before forecast if promotion calendar is planned.",
}


# --- From notebook cell 36 ---

def read_date_table(table_name: str, columns: list[str]) -> pd.DataFrame:
    path = DATA_DIR / f"{table_name}.csv"
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=columns)
    return pd.read_csv(path, usecols=columns, low_memory=False)


def parse_dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def summarize_date_column(table_name: str, date_column: str) -> dict:
    path = DATA_DIR / f"{table_name}.csv"
    if not path.exists() or path.stat().st_size == 0:
        return {
            "table_name": table_name,
            "date_column": date_column,
            "min_date": pd.NaT,
            "max_date": pd.NaT,
            "unique_dates": 0,
            "missing_or_invalid": 0,
        }

    df = pd.read_csv(path, usecols=[date_column], low_memory=False)
    parsed = parse_dates(df[date_column])
    return {
        "table_name": table_name,
        "date_column": date_column,
        "min_date": parsed.min(),
        "max_date": parsed.max(),
        "unique_dates": parsed.nunique(),
        "missing_or_invalid": int(parsed.isna().sum()),
    }


def build_date_range_summary(checks: dict[str, list[str]]) -> pd.DataFrame:
    records = []
    for table_name, date_columns in checks.items():
        for date_column in date_columns:
            records.append(summarize_date_column(table_name, date_column))
    return (
        pd.DataFrame(records)
        .sort_values(["min_date", "table_name", "date_column"], na_position="last")
        .reset_index(drop=True)
    )


def format_sample_rows(df: pd.DataFrame, columns: list[str], max_rows: int = 3) -> str:
    if df.empty:
        return ""
    available_columns = [column for column in columns if column in df.columns]
    sample = df[available_columns].head(max_rows).copy()
    for column in sample.columns:
        if pd.api.types.is_datetime64_any_dtype(sample[column]):
            sample[column] = sample[column].dt.strftime("%Y-%m-%d")
    return str(sample.to_dict("records"))


def summarize_time_rule(
    rule: str,
    df: pd.DataFrame,
    left_date: str,
    right_date: str,
    sample_columns: list[str],
    severity_if_issue: str = "High",
) -> dict:
    if df.empty:
        return {
            "rule": rule,
            "issue_count": 0,
            "issue_pct": 0.0,
            "sample_rows": "",
            "severity": "Not checked",
        }

    work = df.copy()
    work[left_date] = parse_dates(work[left_date])
    work[right_date] = parse_dates(work[right_date])
    valid = work[left_date].notna() & work[right_date].notna()
    issue_mask = valid & (work[left_date] > work[right_date])
    denominator = int(valid.sum())
    issue_count = int(issue_mask.sum())
    issue_pct = round(issue_count / denominator * 100, 4) if denominator else 0.0
    return {
        "rule": rule,
        "issue_count": issue_count,
        "issue_pct": issue_pct,
        "sample_rows": format_sample_rows(work.loc[issue_mask], sample_columns),
        "severity": severity_if_issue if issue_count else "OK",
    }


def build_time_logic_issues() -> pd.DataFrame:
    records = []

    orders = read_date_table("orders", ["order_id", "customer_id", "order_date"])
    customers = read_date_table("customers", ["customer_id", "signup_date"])
    orders_customers = orders.merge(customers, on="customer_id", how="left")
    records.append(
        summarize_time_rule(
            "signup_date <= order_date",
            orders_customers,
            "signup_date",
            "order_date",
            ["order_id", "customer_id", "signup_date", "order_date"],
            severity_if_issue="High",
        )
    )

    shipments = read_date_table("shipments", ["order_id", "ship_date", "delivery_date"])
    order_shipments = shipments.merge(orders[["order_id", "order_date"]], on="order_id", how="left")
    records.append(
        summarize_time_rule(
            "order_date <= ship_date",
            order_shipments,
            "order_date",
            "ship_date",
            ["order_id", "order_date", "ship_date", "delivery_date"],
            severity_if_issue="High",
        )
    )
    records.append(
        summarize_time_rule(
            "ship_date <= delivery_date",
            shipments,
            "ship_date",
            "delivery_date",
            ["order_id", "ship_date", "delivery_date"],
            severity_if_issue="High",
        )
    )

    returns = read_date_table("returns", ["return_id", "order_id", "return_date"])
    order_returns = returns.merge(orders[["order_id", "order_date"]], on="order_id", how="left")
    records.append(
        summarize_time_rule(
            "order_date <= return_date",
            order_returns,
            "order_date",
            "return_date",
            ["return_id", "order_id", "order_date", "return_date"],
            severity_if_issue="High",
        )
    )

    reviews = read_date_table("reviews", ["review_id", "order_id", "review_date"])
    order_reviews = reviews.merge(orders[["order_id", "order_date"]], on="order_id", how="left")
    records.append(
        summarize_time_rule(
            "order_date <= review_date",
            order_reviews,
            "order_date",
            "review_date",
            ["review_id", "order_id", "order_date", "review_date"],
            severity_if_issue="High",
        )
    )

    promotions = read_date_table("promotions", ["promo_id", "start_date", "end_date"])
    records.append(
        summarize_time_rule(
            "start_date <= end_date",
            promotions,
            "start_date",
            "end_date",
            ["promo_id", "start_date", "end_date"],
            severity_if_issue="High",
        )
    )

    return pd.DataFrame(records)


def build_date_continuity_summary(date_range_summary: pd.DataFrame) -> pd.DataFrame:
    records = []
    for row in date_range_summary.itertuples():
        if pd.isna(row.min_date) or pd.isna(row.max_date):
            expected_days = 0
            missing_calendar_days = 0
        else:
            expected_days = int((row.max_date - row.min_date).days) + 1
            missing_calendar_days = max(expected_days - int(row.unique_dates), 0)
        records.append(
            {
                "table_name": row.table_name,
                "date_column": row.date_column,
                "expected_calendar_days": expected_days,
                "unique_dates": int(row.unique_dates),
                "missing_calendar_days": missing_calendar_days,
                "is_continuous_daily": missing_calendar_days == 0 and expected_days > 0,
            }
        )
    return pd.DataFrame(records)


def build_forecast_availability_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"feature": feature, "forecast_note": note}
            for feature, note in FORECAST_AVAILABILITY.items()
        ]
    )


def plot_date_ranges(summary: pd.DataFrame):
    plot_data = summary.dropna(subset=["min_date", "max_date"]).sort_values("min_date")
    fig, ax = plt.subplots(figsize=(10, 5))
    if plot_data.empty:
        ax.text(0.5, 0.5, "No valid date ranges", ha="center", va="center")
        ax.axis("off")
        return fig

    labels = plot_data["table_name"] + "." + plot_data["date_column"]
    left = plot_data["min_date"].map(mdates.date2num)
    widths = (plot_data["max_date"] - plot_data["min_date"]).dt.days.clip(lower=1)
    ax.barh(labels, widths, left=left, color="#4E79A7")
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=30)
    clean_axis(ax, "Date ranges by column", xlabel="calendar period")
    plt.tight_layout()

def plot_time_logic_issues(issues: pd.DataFrame):
    plot_data = issues.sort_values("issue_count", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 4))
    colors = ["#E15759" if value > 0 else "#59A14F" for value in plot_data["issue_count"]]
    ax.barh(plot_data["rule"], plot_data["issue_count"], color=colors)
    clean_axis(ax, "Time logic issues", xlabel="issue rows")
    for index, row in enumerate(plot_data.itertuples()):
        ax.text(row.issue_count + 0.2, index, f"{row.issue_count:,}", va="center", fontsize=8)
    plt.tight_layout()


# --- From notebook cell 46 ---

PRIMARY_KEY_CHECKS = {
    "customers": ["customer_id"],
    "products": ["product_id"],
    "promotions": ["promo_id"],
    "geography": ["zip"],
    "orders": ["order_id"],
    "payments": ["order_id"],
    "shipments": ["order_id"],
    "returns": ["return_id"],
    "reviews": ["review_id"],
    "sales": ["Date"],
}

CANDIDATE_KEY_CHECKS = {
    "order_items": ["order_id", "product_id"],
    "inventory": ["snapshot_date", "product_id"],
    "web_traffic": ["date", "traffic_source"],
}


# --- From notebook cell 47 ---

def duplicate_severity(key_type: str, duplicate_rows: int) -> str:
    if duplicate_rows == 0:
        return "OK"
    if key_type == "primary_key":
        return "High"
    return "Medium"


def duplicate_note(table_name: str, key_columns: list[str], key_type: str, duplicate_rows: int) -> str:
    key_text = " + ".join(key_columns)
    if duplicate_rows == 0:
        return f"{key_text} is unique; joins at this key should not multiply rows."

    if key_type == "primary_key":
        return f"{key_text} is expected to be unique but has duplicates; investigate before joining."

    return (
        f"{key_text} is not unique. This suggests the table grain is more detailed than this "
        "candidate key; aggregate first or add a line-level key before joining."
    )


def check_key_uniqueness(table_name: str, key_columns: list[str], key_type: str) -> dict:
    path = DATA_DIR / f"{table_name}.csv"
    if not path.exists() or path.stat().st_size == 0:
        return {
            "table_name": table_name,
            "key_columns": ", ".join(key_columns),
            "rows": 0,
            "unique_keys": 0,
            "duplicate_rows": 0,
            "severity": "Not checked",
            "note": "File missing or empty.",
        }

    df = pd.read_csv(path, usecols=key_columns, low_memory=False)
    rows = len(df)
    unique_keys = df.drop_duplicates(subset=key_columns).shape[0]
    duplicate_rows = int(df.duplicated(subset=key_columns).sum())
    severity = duplicate_severity(key_type, duplicate_rows)

    return {
        "table_name": table_name,
        "key_columns": ", ".join(key_columns),
        "rows": rows,
        "unique_keys": unique_keys,
        "duplicate_rows": duplicate_rows,
        "severity": severity,
        "note": duplicate_note(table_name, key_columns, key_type, duplicate_rows),
    }


def build_duplicate_key_summary(
    primary_checks: dict[str, list[str]],
    candidate_checks: dict[str, list[str]],
) -> pd.DataFrame:
    records = []
    for table_name, key_columns in primary_checks.items():
        records.append(check_key_uniqueness(table_name, key_columns, "primary_key"))
    for table_name, key_columns in candidate_checks.items():
        records.append(check_key_uniqueness(table_name, key_columns, "candidate_key"))

    severity_order = {"High": 0, "Medium": 1, "OK": 2, "Not checked": 3}
    summary = pd.DataFrame(records)
    return (
        summary.assign(severity_rank=lambda df: df["severity"].map(severity_order).fillna(9))
        .sort_values(["severity_rank", "duplicate_rows", "table_name"], ascending=[True, False, True])
        .drop(columns="severity_rank")
        .reset_index(drop=True)
    )


def build_duplicate_key_examples(
    table_name: str,
    key_columns: list[str],
    top_n: int = 20,
) -> pd.DataFrame:
    path = DATA_DIR / f"{table_name}.csv"
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()

    df = pd.read_csv(path, low_memory=False)
    duplicate_mask = df.duplicated(subset=key_columns, keep=False)
    return df.loc[duplicate_mask].sort_values(key_columns).head(top_n).reset_index(drop=True)


def plot_duplicate_rows(summary: pd.DataFrame):
    plot_data = summary.sort_values("duplicate_rows", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#E15759" if value > 0 else "#59A14F" for value in plot_data["duplicate_rows"]]
    ax.barh(plot_data["table_name"], plot_data["duplicate_rows"], color=colors)
    clean_axis(ax, "Duplicate rows by checked key", xlabel="duplicate rows")
    for index, row in enumerate(plot_data.itertuples()):
        ax.text(row.duplicate_rows + 0.2, index, f"{row.duplicate_rows:,}", va="center", fontsize=8)
    plt.tight_layout()


def plot_duplicate_severity(summary: pd.DataFrame):
    severity_order = ["OK", "Medium", "High", "Not checked"]
    counts = summary["severity"].value_counts().reindex(severity_order).dropna()
    fig, ax = plt.subplots(figsize=(7, 3.5))
    color_map = {
        "OK": "#59A14F",
        "Medium": "#F28E2B",
        "High": "#E15759",
        "Not checked": "#9D9D9D",
    }
    ax.bar(counts.index, counts.values, color=[color_map.get(value, "#9D9D9D") for value in counts.index])
    clean_axis(ax, "Key check severity", ylabel="checked keys")
    for index, value in enumerate(counts.values):
        ax.text(index, value + 0.05, int(value), ha="center", fontsize=9)
    plt.tight_layout()


def check_relationship(
    child_table: str,
    child_key: str,
    parent_table: str,
    parent_key: str,
    relationship: str,
) -> dict:
    child_path = DATA_DIR / f"{child_table}.csv"
    parent_path = DATA_DIR / f"{parent_table}.csv"

    if not child_path.exists() or not parent_path.exists() or child_path.stat().st_size == 0 or parent_path.stat().st_size == 0:
        return {
            "child_table": child_table,
            "child_key": child_key,
            "parent_table": parent_table,
            "parent_key": parent_key,
            "relationship": relationship,
            "child_rows": 0,
            "child_non_null_rows": 0,
            "parent_rows": 0,
            "parent_unique_keys": 0,
            "parent_duplicate_rows": 0,
            "orphan_rows": 0,
            "orphan_pct": 0.0,
            "severity": "Not checked",
            "note": "Child or parent file missing/empty.",
        }

    child = pd.read_csv(child_path, usecols=[child_key], low_memory=False)
    parent = pd.read_csv(parent_path, usecols=[parent_key], low_memory=False)
    child_values = child[child_key].dropna()
    parent_values = parent[parent_key].dropna()
    parent_value_set = set(parent_values)
    orphan_mask = ~child_values.isin(parent_value_set)

    parent_duplicate_rows = int(parent.duplicated(subset=[parent_key]).sum())
    orphan_rows = int(orphan_mask.sum())
    orphan_pct = round(orphan_rows / max(len(child_values), 1) * 100, 4)

    if parent_duplicate_rows > 0:
        severity = "High"
        note = "Parent key has duplicates; joins may multiply rows."
    elif orphan_rows > 0:
        severity = "High"
        note = "Child table contains keys missing from parent; join may lose/enrich incorrectly."
    else:
        severity = "OK"
        if "zero-or-one" in relationship:
            note = "No orphan keys among non-null optional relationship values."
        else:
            note = "No orphan keys; relationship is join-safe at checked key."

    return {
        "child_table": child_table,
        "child_key": child_key,
        "parent_table": parent_table,
        "parent_key": parent_key,
        "relationship": relationship,
        "child_rows": len(child),
        "child_non_null_rows": len(child_values),
        "parent_rows": len(parent),
        "parent_unique_keys": parent_values.nunique(dropna=True),
        "parent_duplicate_rows": parent_duplicate_rows,
        "orphan_rows": orphan_rows,
        "orphan_pct": orphan_pct,
        "severity": severity,
        "note": note,
    }


def build_relationship_checks(relationships: list[tuple] = RELATIONSHIPS) -> pd.DataFrame:
    severity_order = {"High": 0, "Medium": 1, "Low": 2, "OK": 3, "Not checked": 4}
    summary = pd.DataFrame([check_relationship(*relationship) for relationship in relationships])
    return (
        summary.assign(severity_rank=lambda df: df["severity"].map(severity_order).fillna(9))
        .sort_values(["severity_rank", "orphan_rows", "child_table", "child_key"], ascending=[True, False, True, True])
        .drop(columns="severity_rank")
        .reset_index(drop=True)
    )


def plot_relationship_orphans(relationship_checks: pd.DataFrame):
    plot_data = relationship_checks.sort_values("orphan_rows", ascending=True).copy()
    labels = plot_data["child_table"] + "." + plot_data["child_key"] + " -> " + plot_data["parent_table"]
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#E15759" if value > 0 else "#59A14F" for value in plot_data["orphan_rows"]]
    ax.barh(labels, plot_data["orphan_rows"], color=colors)
    clean_axis(ax, "Foreign key orphan rows", xlabel="orphan rows")
    for index, row in enumerate(plot_data.itertuples()):
        ax.text(row.orphan_rows + 0.2, index, f"{row.orphan_rows:,}", va="center", fontsize=8)
    plt.tight_layout()


def plot_relationship_status(relationship_checks: pd.DataFrame):
    counts = relationship_checks["severity"].value_counts().reindex(["OK", "Low", "Medium", "High", "Not checked"]).dropna()
    color_map = {
        "OK": "#59A14F",
        "Low": "#76B7B2",
        "Medium": "#F28E2B",
        "High": "#E15759",
        "Not checked": "#9D9D9D",
    }
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(counts.index, counts.values, color=[color_map.get(value, "#9D9D9D") for value in counts.index])
    clean_axis(ax, "Relationship check severity", ylabel="relationships")
    for index, value in enumerate(counts.values):
        ax.text(index, value + 0.05, int(value), ha="center", fontsize=9)
    plt.tight_layout()


# --- From notebook cell 54 ---

BUSINESS_RULES = [
    {
        "table_name": "products",
        "rule": "products.price > 0",
        "columns": ["product_id", "price"],
        "issue_condition": lambda df: df["price"] <= 0,
        "severity_if_issue": "High",
        "note_if_ok": "All product prices are positive.",
        "note_if_issue": "Product price must be positive before revenue/profit analysis.",
    },
    {
        "table_name": "products",
        "rule": "products.cogs > 0",
        "columns": ["product_id", "cogs"],
        "issue_condition": lambda df: df["cogs"] <= 0,
        "severity_if_issue": "High",
        "note_if_ok": "All product COGS values are positive.",
        "note_if_issue": "Product COGS must be positive before profit analysis.",
    },
    {
        "table_name": "products",
        "rule": "products.cogs < products.price",
        "columns": ["product_id", "price", "cogs"],
        "issue_condition": lambda df: df["cogs"] >= df["price"],
        "severity_if_issue": "High",
        "note_if_ok": "No product has COGS greater than or equal to price.",
        "note_if_issue": "Product-level margin is non-positive; investigate price or COGS.",
    },
    {
        "table_name": "order_items",
        "rule": "order_items.quantity > 0",
        "columns": ["order_id", "product_id", "quantity"],
        "issue_condition": lambda df: df["quantity"] <= 0,
        "severity_if_issue": "High",
        "note_if_ok": "All order item quantities are positive.",
        "note_if_issue": "Quantity must be positive for line revenue.",
    },
    {
        "table_name": "order_items",
        "rule": "order_items.unit_price > 0",
        "columns": ["order_id", "product_id", "unit_price"],
        "issue_condition": lambda df: df["unit_price"] <= 0,
        "severity_if_issue": "High",
        "note_if_ok": "All unit prices are positive.",
        "note_if_issue": "Unit price must be positive for line revenue.",
    },
    {
        "table_name": "order_items",
        "rule": "order_items.discount_amount >= 0",
        "columns": ["order_id", "product_id", "discount_amount"],
        "issue_condition": lambda df: df["discount_amount"] < 0,
        "severity_if_issue": "High",
        "note_if_ok": "No negative discounts found.",
        "note_if_issue": "Negative discount would inflate net revenue; investigate.",
    },
    {
        "table_name": "order_items",
        "rule": "order_items.discount_amount <= quantity * unit_price",
        "columns": ["order_id", "product_id", "quantity", "unit_price", "discount_amount"],
        "issue_condition": lambda df: df["discount_amount"] > df["quantity"] * df["unit_price"],
        "severity_if_issue": "High",
        "note_if_ok": "No discount exceeds gross line value.",
        "note_if_issue": "Discount exceeds line value; net revenue would become negative.",
    },
    {
        "table_name": "payments",
        "rule": "payments.payment_value >= 0",
        "columns": ["order_id", "payment_value"],
        "issue_condition": lambda df: df["payment_value"] < 0,
        "severity_if_issue": "High",
        "note_if_ok": "No negative payment values found.",
        "note_if_issue": "Negative payment value needs payment/refund definition review.",
    },
    {
        "table_name": "shipments",
        "rule": "shipments.shipping_fee >= 0",
        "columns": ["order_id", "shipping_fee"],
        "issue_condition": lambda df: df["shipping_fee"] < 0,
        "severity_if_issue": "Medium",
        "note_if_ok": "No negative shipping fees found.",
        "note_if_issue": "Negative shipping fee may represent adjustment or data issue.",
    },
    {
        "table_name": "returns",
        "rule": "returns.return_quantity > 0",
        "columns": ["return_id", "order_id", "product_id", "return_quantity"],
        "issue_condition": lambda df: df["return_quantity"] <= 0,
        "severity_if_issue": "High",
        "note_if_ok": "All return quantities are positive.",
        "note_if_issue": "Return quantity must be positive for refund analysis.",
    },
    {
        "table_name": "returns",
        "rule": "returns.refund_amount >= 0",
        "columns": ["return_id", "order_id", "product_id", "refund_amount"],
        "issue_condition": lambda df: df["refund_amount"] < 0,
        "severity_if_issue": "High",
        "note_if_ok": "No negative refund amounts found.",
        "note_if_issue": "Negative refund amount needs definition review.",
    },
    {
        "table_name": "reviews",
        "rule": "reviews.rating between 1 and 5",
        "columns": ["review_id", "order_id", "product_id", "rating"],
        "issue_condition": lambda df: ~df["rating"].between(1, 5),
        "severity_if_issue": "Medium",
        "note_if_ok": "All ratings are within 1 to 5.",
        "note_if_issue": "Rating outside 1 to 5 should be corrected or excluded.",
    },
    {
        "table_name": "sales",
        "rule": "sales.Revenue > 0",
        "columns": ["Date", "Revenue"],
        "issue_condition": lambda df: df["Revenue"] <= 0,
        "severity_if_issue": "High",
        "note_if_ok": "All daily Revenue values are positive.",
        "note_if_issue": "Non-positive Revenue directly affects revenue analysis.",
    },
    {
        "table_name": "sales",
        "rule": "sales.COGS > 0",
        "columns": ["Date", "COGS"],
        "issue_condition": lambda df: df["COGS"] <= 0,
        "severity_if_issue": "High",
        "note_if_ok": "All daily COGS values are positive.",
        "note_if_issue": "Non-positive COGS directly affects profit analysis.",
    },
    {
        "table_name": "sales",
        "rule": "sales.COGS <= sales.Revenue",
        "columns": ["Date", "Revenue", "COGS"],
        "issue_condition": lambda df: df["COGS"] > df["Revenue"],
        "severity_if_issue": "Medium",
        "note_if_ok": "No daily negative gross margin found.",
        "note_if_issue": "COGS exceeds Revenue. This may be a real negative-margin day, not automatically a data error.",
    },
    {
        "table_name": "inventory",
        "rule": "inventory.stock_on_hand >= 0",
        "columns": ["snapshot_date", "product_id", "stock_on_hand"],
        "issue_condition": lambda df: df["stock_on_hand"] < 0,
        "severity_if_issue": "Medium",
        "note_if_ok": "No negative stock_on_hand values found.",
        "note_if_issue": "Negative stock needs inventory definition review.",
    },
    {
        "table_name": "inventory",
        "rule": "inventory.units_received >= 0",
        "columns": ["snapshot_date", "product_id", "units_received"],
        "issue_condition": lambda df: df["units_received"] < 0,
        "severity_if_issue": "Medium",
        "note_if_ok": "No negative units_received values found.",
        "note_if_issue": "Negative received units need inventory definition review.",
    },
    {
        "table_name": "inventory",
        "rule": "inventory.units_sold >= 0",
        "columns": ["snapshot_date", "product_id", "units_sold"],
        "issue_condition": lambda df: df["units_sold"] < 0,
        "severity_if_issue": "Medium",
        "note_if_ok": "No negative units_sold values found.",
        "note_if_issue": "Negative sold units need inventory definition review.",
    },
    {
        "table_name": "inventory",
        "rule": "inventory.stockout_days >= 0",
        "columns": ["snapshot_date", "product_id", "stockout_days"],
        "issue_condition": lambda df: df["stockout_days"] < 0,
        "severity_if_issue": "Medium",
        "note_if_ok": "No negative stockout_days values found.",
        "note_if_issue": "Negative stockout_days is not valid.",
    },
    {
        "table_name": "inventory",
        "rule": "inventory.fill_rate between 0 and 1",
        "columns": ["snapshot_date", "product_id", "fill_rate"],
        "issue_condition": lambda df: ~df["fill_rate"].between(0, 1),
        "severity_if_issue": "Medium",
        "note_if_ok": "All fill_rate values are between 0 and 1.",
        "note_if_issue": "fill_rate outside 0 to 1 is invalid.",
    },
    {
        "table_name": "inventory",
        "rule": "inventory.sell_through_rate between 0 and 1",
        "columns": ["snapshot_date", "product_id", "sell_through_rate"],
        "issue_condition": lambda df: ~df["sell_through_rate"].between(0, 1),
        "severity_if_issue": "Medium",
        "note_if_ok": "All sell_through_rate values are between 0 and 1.",
        "note_if_issue": "sell_through_rate outside 0 to 1 is invalid.",
    },
]


# --- From notebook cell 55 ---

def evaluate_business_rule(rule_config: dict) -> dict:
    table_name = rule_config["table_name"]
    path = DATA_DIR / f"{table_name}.csv"
    rule_text = rule_config["rule"]

    if not path.exists() or path.stat().st_size == 0:
        return {
            "table_name": table_name,
            "rule": rule_text,
            "issue_count": 0,
            "issue_pct": 0.0,
            "severity": "Not checked",
            "note": "File missing or empty.",
        }

    df = pd.read_csv(path, usecols=rule_config["columns"], low_memory=False)
    issue_mask = rule_config["issue_condition"](df).fillna(False)
    issue_count = int(issue_mask.sum())
    issue_pct = round(issue_count / max(len(df), 1) * 100, 4)
    severity = rule_config["severity_if_issue"] if issue_count else "OK"
    note = rule_config["note_if_issue"] if issue_count else rule_config["note_if_ok"]

    return {
        "table_name": table_name,
        "rule": rule_text,
        "issue_count": issue_count,
        "issue_pct": issue_pct,
        "severity": severity,
        "note": note,
    }


def build_business_rule_issues(rule_configs: list[dict]) -> pd.DataFrame:
    severity_order = {"High": 0, "Medium": 1, "Low": 2, "OK": 3, "Not checked": 4}
    summary = pd.DataFrame([evaluate_business_rule(rule) for rule in rule_configs])
    return (
        summary.assign(severity_rank=lambda df: df["severity"].map(severity_order).fillna(9))
        .sort_values(["severity_rank", "issue_count", "table_name", "rule"], ascending=[True, False, True, True])
        .drop(columns="severity_rank")
        .reset_index(drop=True)
    )


def build_business_rule_examples(rule_configs: list[dict], max_rows_per_rule: int = 5) -> pd.DataFrame:
    examples = []
    for rule_config in rule_configs:
        path = DATA_DIR / f"{rule_config['table_name']}.csv"
        if not path.exists() or path.stat().st_size == 0:
            continue

        df = pd.read_csv(path, usecols=rule_config["columns"], low_memory=False)
        issue_mask = rule_config["issue_condition"](df).fillna(False)
        if not issue_mask.any():
            continue

        sample = df.loc[issue_mask].head(max_rows_per_rule).copy()
        sample.insert(0, "rule", rule_config["rule"])
        sample.insert(0, "table_name", rule_config["table_name"])
        examples.append(sample)

    return pd.concat(examples, ignore_index=True) if examples else pd.DataFrame()


def plot_business_rule_issues(summary: pd.DataFrame):
    plot_data = summary.query("issue_count > 0").sort_values("issue_count", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 3.5))
    if plot_data.empty:
        ax.text(0.5, 0.5, "No business rule issues found", ha="center", va="center")
        ax.axis("off")
        return fig

    labels = plot_data["table_name"] + " - " + plot_data["rule"]
    colors = ["#E15759" if value == "High" else "#F28E2B" for value in plot_data["severity"]]
    ax.barh(labels, plot_data["issue_count"], color=colors)
    clean_axis(ax, "Business rule issues", xlabel="issue rows")
    for index, row in enumerate(plot_data.itertuples()):
        ax.text(row.issue_count * 1.01, index, f"{row.issue_count:,}", va="center", fontsize=8)
    plt.tight_layout()


def plot_business_rule_severity(summary: pd.DataFrame):
    severity_order = ["OK", "Medium", "High", "Not checked"]
    counts = summary["severity"].value_counts().reindex(severity_order).dropna()
    color_map = {
        "OK": "#59A14F",
        "Medium": "#F28E2B",
        "High": "#E15759",
        "Not checked": "#9D9D9D",
    }

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(counts.index, counts.values, color=[color_map.get(value, "#9D9D9D") for value in counts.index])
    clean_axis(ax, "Business rule severity", ylabel="rules")
    for index, value in enumerate(counts.values):
        ax.text(index, value + 0.05, int(value), ha="center", fontsize=9)
    plt.tight_layout()


# --- From notebook cell 63 ---

EXPECTED_SHIPMENT_STATUSES = {"shipped", "delivered", "returned"}
EXPECTED_RETURN_STATUSES = {"returned"}
EXPECTED_REVIEW_STATUSES = {"delivered", "returned"}

LIFECYCLE_RULES = [
    {
        "rule": "cancelled orders should not have shipment",
        "issue_condition": lambda df: df["order_status"].eq("cancelled") & df["has_shipment"],
        "severity_if_issue": "High",
        "note_if_ok": "No cancelled order has shipment.",
        "note_if_issue": "Cancelled order has shipment record; status conflicts with fulfillment.",
    },
    {
        "rule": "created/paid orders should not have delivery_date",
        "issue_condition": lambda df: df["order_status"].isin(["created", "paid"]) & df["delivery_date"].notna(),
        "severity_if_issue": "High",
        "note_if_ok": "No created/paid order has delivery_date.",
        "note_if_issue": "Early lifecycle order already has delivery_date.",
    },
    {
        "rule": "shipped orders should have shipment",
        "issue_condition": lambda df: df["order_status"].eq("shipped") & ~df["has_shipment"],
        "severity_if_issue": "High",
        "note_if_ok": "All shipped orders have shipment record.",
        "note_if_issue": "Shipped order has no shipment record.",
    },
    {
        "rule": "delivered orders should have shipment",
        "issue_condition": lambda df: df["order_status"].eq("delivered") & ~df["has_shipment"],
        "severity_if_issue": "High",
        "note_if_ok": "All delivered orders have shipment record.",
        "note_if_issue": "Delivered order has no shipment record.",
    },
    {
        "rule": "returned orders should have return record",
        "issue_condition": lambda df: df["order_status"].eq("returned") & ~df["has_return"],
        "severity_if_issue": "High",
        "note_if_ok": "All returned orders have return record.",
        "note_if_issue": "Returned status exists without return table record.",
    },
    {
        "rule": "returned orders should have shipment",
        "issue_condition": lambda df: df["order_status"].eq("returned") & ~df["has_shipment"],
        "severity_if_issue": "High",
        "note_if_ok": "All returned orders have shipment record.",
        "note_if_issue": "Returned order has no shipment record.",
    },
    {
        "rule": "delivered orders should have delivery_date",
        "issue_condition": lambda df: df["order_status"].eq("delivered") & df["delivery_date"].isna(),
        "severity_if_issue": "High",
        "note_if_ok": "All delivered orders have delivery_date.",
        "note_if_issue": "Delivered order has missing delivery_date.",
    },
    {
        "rule": "shipment should only appear for shipped/delivered/returned",
        "issue_condition": lambda df: df["has_shipment"] & ~df["order_status"].isin(EXPECTED_SHIPMENT_STATUSES),
        "severity_if_issue": "High",
        "note_if_ok": "Shipment only appears in shipped/delivered/returned statuses.",
        "note_if_issue": "Shipment appears in an unexpected order status.",
    },
    {
        "rule": "return should only appear for returned",
        "issue_condition": lambda df: df["has_return"] & ~df["order_status"].isin(EXPECTED_RETURN_STATUSES),
        "severity_if_issue": "High",
        "note_if_ok": "Return records only appear in returned status.",
        "note_if_issue": "Return record appears outside returned status.",
    },
    {
        "rule": "review should only appear for delivered/returned",
        "issue_condition": lambda df: df["has_review"] & ~df["order_status"].isin(EXPECTED_REVIEW_STATUSES),
        "severity_if_issue": "Medium",
        "note_if_ok": "Review records only appear in delivered/returned statuses.",
        "note_if_issue": "Review record appears before delivery/return lifecycle.",
    },
]


# --- From notebook cell 64 ---

def build_order_lifecycle_table() -> pd.DataFrame:
    orders = pd.read_csv(DATA_DIR / "orders.csv", usecols=["order_id", "order_status"], low_memory=False)
    payments = pd.read_csv(DATA_DIR / "payments.csv", usecols=["order_id"], low_memory=False)
    shipments = pd.read_csv(
        DATA_DIR / "shipments.csv",
        usecols=["order_id", "ship_date", "delivery_date"],
        low_memory=False,
    )
    returns = pd.read_csv(DATA_DIR / "returns.csv", usecols=["order_id"], low_memory=False)
    reviews = pd.read_csv(DATA_DIR / "reviews.csv", usecols=["order_id"], low_memory=False)

    payment_orders = payments.drop_duplicates("order_id").assign(has_payment=True)
    shipment_orders = shipments.drop_duplicates("order_id").assign(has_shipment=True)
    return_orders = returns.drop_duplicates("order_id").assign(has_return=True)
    review_orders = reviews.drop_duplicates("order_id").assign(has_review=True)

    lifecycle = (
        orders.merge(payment_orders, on="order_id", how="left")
        .merge(shipment_orders, on="order_id", how="left")
        .merge(return_orders, on="order_id", how="left")
        .merge(review_orders, on="order_id", how="left")
    )

    for column in ["has_payment", "has_shipment", "has_return", "has_review"]:
        lifecycle[column] = lifecycle[column].fillna(False).astype(bool)
    lifecycle["delivery_date"] = pd.to_datetime(lifecycle["delivery_date"], errors="coerce")
    lifecycle["ship_date"] = pd.to_datetime(lifecycle["ship_date"], errors="coerce")
    return lifecycle


def build_order_status_summary(lifecycle: pd.DataFrame) -> pd.DataFrame:
    total_orders = len(lifecycle)
    summary = (
        lifecycle.groupby("order_status", dropna=False)
        .agg(
            orders=("order_id", "size"),
            has_payment_pct=("has_payment", "mean"),
            has_shipment_pct=("has_shipment", "mean"),
            has_return_pct=("has_return", "mean"),
            has_review_pct=("has_review", "mean"),
            delivery_date_missing_pct=("delivery_date", lambda value: value.isna().mean()),
        )
        .reset_index()
    )
    summary["order_pct"] = summary["orders"] / max(total_orders, 1)
    pct_columns = [
        "order_pct",
        "has_payment_pct",
        "has_shipment_pct",
        "has_return_pct",
        "has_review_pct",
        "delivery_date_missing_pct",
    ]
    summary[pct_columns] = summary[pct_columns] * 100
    return summary.sort_values("orders", ascending=False).reset_index(drop=True)


def build_payment_order_check() -> pd.DataFrame:
    orders = pd.read_csv(DATA_DIR / "orders.csv", usecols=["order_id"], low_memory=False)
    payments = pd.read_csv(DATA_DIR / "payments.csv", usecols=["order_id"], low_memory=False)

    order_ids = set(orders["order_id"])
    payment_ids = set(payments["order_id"])
    payment_duplicate_rows = int(payments.duplicated("order_id").sum())

    records = [
        {
            "check": "orders without payment",
            "count": len(order_ids - payment_ids),
            "severity": "High" if order_ids - payment_ids else "OK",
            "note": "Every order should have one payment record.",
        },
        {
            "check": "payments without order",
            "count": len(payment_ids - order_ids),
            "severity": "High" if payment_ids - order_ids else "OK",
            "note": "Every payment should map to an order.",
        },
        {
            "check": "duplicate payment order_id",
            "count": payment_duplicate_rows,
            "severity": "High" if payment_duplicate_rows else "OK",
            "note": "Payment is expected to be 1:1 with orders.",
        },
    ]
    return pd.DataFrame(records)


def format_lifecycle_samples(df: pd.DataFrame, max_rows: int = 3) -> str:
    if df.empty:
        return ""
    sample_columns = [
        "order_id",
        "order_status",
        "has_payment",
        "has_shipment",
        "has_return",
        "has_review",
        "ship_date",
        "delivery_date",
    ]
    sample = df[[column for column in sample_columns if column in df.columns]].head(max_rows).copy()
    for column in ["ship_date", "delivery_date"]:
        if column in sample.columns:
            sample[column] = sample[column].dt.strftime("%Y-%m-%d")
    return str(sample.to_dict("records"))


def evaluate_lifecycle_rule(lifecycle: pd.DataFrame, rule_config: dict) -> dict:
    issue_mask = rule_config["issue_condition"](lifecycle).fillna(False)
    issue_count = int(issue_mask.sum())
    issue_pct = round(issue_count / max(len(lifecycle), 1) * 100, 4)
    return {
        "rule": rule_config["rule"],
        "issue_count": issue_count,
        "issue_pct": issue_pct,
        "sample_rows": format_lifecycle_samples(lifecycle.loc[issue_mask]),
        "severity": rule_config["severity_if_issue"] if issue_count else "OK",
        "note": rule_config["note_if_issue"] if issue_count else rule_config["note_if_ok"],
    }


def build_lifecycle_consistency_issues(lifecycle: pd.DataFrame) -> pd.DataFrame:
    severity_order = {"High": 0, "Medium": 1, "Low": 2, "OK": 3}
    summary = pd.DataFrame([evaluate_lifecycle_rule(lifecycle, rule) for rule in LIFECYCLE_RULES])
    return (
        summary.assign(severity_rank=lambda df: df["severity"].map(severity_order).fillna(9))
        .sort_values(["severity_rank", "issue_count", "rule"], ascending=[True, False, True])
        .drop(columns="severity_rank")
        .reset_index(drop=True)
    )


def plot_order_status_distribution(status_summary: pd.DataFrame):
    plot_data = status_summary.sort_values("orders", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(plot_data["order_status"], plot_data["orders"], color="#4E79A7")
    clean_axis(ax, "Orders by status", xlabel="orders")
    for index, row in enumerate(plot_data.itertuples()):
        ax.text(row.orders * 1.01, index, f"{row.orders:,} ({row.order_pct:.1f}%)", va="center", fontsize=8)
    plt.tight_layout()
    return fig


def plot_lifecycle_issue_counts(issue_summary: pd.DataFrame):
    plot_data = issue_summary.query("issue_count > 0").sort_values("issue_count", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 4))
    if plot_data.empty:
        ax.text(0.5, 0.5, "No lifecycle consistency issues found", ha="center", va="center")
        ax.axis("off")
        return fig

    colors = ["#E15759" if severity == "High" else "#F28E2B" for severity in plot_data["severity"]]
    ax.barh(plot_data["rule"], plot_data["issue_count"], color=colors)
    clean_axis(ax, "Lifecycle consistency issues", xlabel="orders")
    for index, row in enumerate(plot_data.itertuples()):
        ax.text(row.issue_count * 1.01, index, f"{row.issue_count:,}", va="center", fontsize=8)
    plt.tight_layout()
    return fig


# --- From notebook cell 73 ---

STATUS_FILTERS = {
    "all orders": lambda df: pd.Series(True, index=df.index),
    "delivered only": lambda df: df["order_status"].eq("delivered"),
    "delivered + returned": lambda df: df["order_status"].isin(["delivered", "returned"]),
    "non-cancelled orders": lambda df: ~df["order_status"].eq("cancelled"),
    "paid/shipped/delivered/returned": lambda df: df["order_status"].isin(
        ["paid", "shipped", "delivered", "returned"]
    ),
}

SALES_COMPARISONS = [
    {
        "compared_metric": "sales.Revenue vs gross_revenue",
        "target_column": "Revenue",
        "candidate_column": "gross_revenue",
    },
    {
        "compared_metric": "sales.Revenue vs net_revenue",
        "target_column": "Revenue",
        "candidate_column": "net_revenue",
    },
    {
        "compared_metric": "sales.Revenue vs payment_value",
        "target_column": "Revenue",
        "candidate_column": "payment_value",
    },
    {
        "compared_metric": "sales.COGS vs calculated_cogs",
        "target_column": "COGS",
        "candidate_column": "calculated_cogs",
    },
]


# --- From notebook cell 74 ---

def build_sales_transaction_base() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    orders = pd.read_csv(
        DATA_DIR / "orders.csv",
        usecols=["order_id", "order_date", "order_status"],
        parse_dates=["order_date"],
        low_memory=False,
    )
    order_items = pd.read_csv(
        DATA_DIR / "order_items.csv",
        usecols=["order_id", "product_id", "quantity", "unit_price", "discount_amount"],
        low_memory=False,
    )
    products = pd.read_csv(DATA_DIR / "products.csv", usecols=["product_id", "cogs"], low_memory=False)
    payments = pd.read_csv(DATA_DIR / "payments.csv", usecols=["order_id", "payment_value"], low_memory=False)
    sales = pd.read_csv(DATA_DIR / "sales.csv", parse_dates=["Date"], low_memory=False)

    item_base = (
        order_items.merge(products, on="product_id", how="left", validate="many_to_one")
        .merge(orders, on="order_id", how="left", validate="many_to_one")
    )
    item_base["gross_revenue"] = item_base["quantity"] * item_base["unit_price"]
    item_base["net_revenue"] = item_base["gross_revenue"] - item_base["discount_amount"]
    item_base["calculated_cogs"] = item_base["quantity"] * item_base["cogs"]

    payment_base = orders.merge(payments, on="order_id", how="left", validate="one_to_one")
    return sales, item_base, payment_base


def aggregate_transactions_by_date(
    sales: pd.DataFrame,
    item_base: pd.DataFrame,
    payment_base: pd.DataFrame,
    status_filter_name: str,
) -> pd.DataFrame:
    item_filter = STATUS_FILTERS[status_filter_name](item_base)
    payment_filter = STATUS_FILTERS[status_filter_name](payment_base)

    daily_items = (
        item_base.loc[item_filter]
        .groupby("order_date")
        .agg(
            gross_revenue=("gross_revenue", "sum"),
            net_revenue=("net_revenue", "sum"),
            calculated_cogs=("calculated_cogs", "sum"),
        )
        .reset_index()
        .rename(columns={"order_date": "Date"})
    )

    daily_payments = (
        payment_base.loc[payment_filter]
        .groupby("order_date")
        .agg(payment_value=("payment_value", "sum"))
        .reset_index()
        .rename(columns={"order_date": "Date"})
    )

    return (
        sales.merge(daily_items, on="Date", how="left")
        .merge(daily_payments, on="Date", how="left")
        .fillna(
            {
                "gross_revenue": 0,
                "net_revenue": 0,
                "calculated_cogs": 0,
                "payment_value": 0,
            }
        )
    )


def compare_metric(daily: pd.DataFrame, target_column: str, candidate_column: str) -> dict:
    target = daily[target_column]
    candidate = daily[candidate_column]
    error = candidate - target
    denominator = target.replace(0, pd.NA)
    mean_percentage_error = (error / denominator).dropna().mean() * 100

    return {
        "MAE": error.abs().mean(),
        "median_AE": error.abs().median(),
        "MPE": mean_percentage_error,
        "correlation": target.corr(candidate),
        "max_AE": error.abs().max(),
    }


def consistency_note(status_filter: str, compared_metric: str, mae: float) -> str:
    if status_filter == "all orders" and mae < 0.01:
        return "Exact reconciliation; sales.csv appears to use this all-order definition."
    if status_filter == "all orders" and "net_revenue" in compared_metric:
        return "Difference equals discount impact; sales.csv is not a net revenue view."
    if status_filter == "all orders" and "payment_value" in compared_metric:
        return "Payment value aligns with net revenue here, not with sales gross Revenue."
    return "Status-filtered subset is expected to differ from total sales.csv."


def build_sales_transaction_consistency() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    sales, item_base, payment_base = build_sales_transaction_base()
    daily_by_filter = {}
    records = []

    for status_filter in STATUS_FILTERS:
        daily = aggregate_transactions_by_date(sales, item_base, payment_base, status_filter)
        daily_by_filter[status_filter] = daily
        for comparison in SALES_COMPARISONS:
            metrics = compare_metric(
                daily,
                comparison["target_column"],
                comparison["candidate_column"],
            )
            records.append(
                {
                    "status_filter": status_filter,
                    "compared_metric": comparison["compared_metric"],
                    **metrics,
                    "note": consistency_note(status_filter, comparison["compared_metric"], metrics["MAE"]),
                }
            )

    summary = pd.DataFrame(records)
    return summary.sort_values(["compared_metric", "MAE"]).reset_index(drop=True), daily_by_filter


def count_affected_dates(daily: pd.DataFrame, target_column: str, candidate_column: str, tolerance: float = 0.01) -> int:
    return int(((daily[candidate_column] - daily[target_column]).abs() > tolerance).sum())


def build_sales_transaction_issues(
    consistency: pd.DataFrame,
    daily_by_filter: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    all_orders = daily_by_filter["all orders"]
    gross_affected = count_affected_dates(all_orders, "Revenue", "gross_revenue")
    cogs_affected = count_affected_dates(all_orders, "COGS", "calculated_cogs")
    net_affected = count_affected_dates(all_orders, "Revenue", "net_revenue")
    payment_affected = count_affected_dates(all_orders, "Revenue", "payment_value")

    return pd.DataFrame(
        [
            {
                "issue": "sales.Revenue vs all-order gross_revenue mismatch",
                "affected_dates": gross_affected,
                "severity": "OK" if gross_affected == 0 else "High",
                "decision": "Use sales.Revenue as all-order gross revenue baseline.",
                "reason": "sales.Revenue reconciles exactly to quantity * unit_price across all orders.",
            },
            {
                "issue": "sales.COGS vs all-order calculated_cogs mismatch",
                "affected_dates": cogs_affected,
                "severity": "OK" if cogs_affected == 0 else "High",
                "decision": "Use sales.COGS as all-order COGS baseline.",
                "reason": "sales.COGS reconciles to quantity * products.cogs within rounding tolerance.",
            },
            {
                "issue": "sales.Revenue differs from net_revenue",
                "affected_dates": net_affected,
                "severity": "Low",
                "decision": "Document definition difference.",
                "reason": "sales.csv stores gross revenue before discount, while net_revenue subtracts discount_amount.",
            },
            {
                "issue": "sales.Revenue differs from payment_value",
                "affected_dates": payment_affected,
                "severity": "Low",
                "decision": "Do not use payment_value as direct replacement for sales.Revenue.",
                "reason": "payment_value follows discounted/net order value in this data, not gross Revenue.",
            },
            {
                "issue": "status-filtered transaction subsets differ from sales.csv totals",
                "affected_dates": int(
                    consistency.query("status_filter != 'all orders' and MAE > 0.01")[
                        "status_filter"
                    ].nunique()
                ),
                "severity": "Low",
                "decision": "Treat as expected unless analysis intentionally filters statuses.",
                "reason": "sales.csv appears to be generated from all orders, so delivered-only/non-cancelled subsets will not match totals.",
            },
        ]
    )


def plot_sales_transaction_mae(consistency: pd.DataFrame):
    plot_data = consistency.sort_values("MAE", ascending=True)
    labels = plot_data["status_filter"] + " | " + plot_data["compared_metric"]
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(labels, plot_data["MAE"], color="#4E79A7")
    clean_axis(ax, "Sales vs transaction MAE", xlabel="mean absolute error")
    plt.tight_layout()


def plot_sales_vs_gross_revenue(daily_by_filter: dict[str, pd.DataFrame]):
    daily = daily_by_filter["all orders"]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(daily["Date"], daily["Revenue"], label="sales.Revenue", color="#4E79A7", linewidth=1.4)
    ax.plot(daily["Date"], daily["gross_revenue"], label="transaction gross_revenue", color="#F28E2B", linewidth=1, linestyle="--")
    clean_axis(ax, "sales.Revenue vs all-order gross_revenue", xlabel="date", ylabel="value")
    ax.legend(frameon=False)
    plt.tight_layout()


# --- From notebook cell 82 ---

OUTLIER_TARGETS = [
    {"table_name": "products", "column": "price", "invalid_condition": lambda s: s <= 0},
    {"table_name": "products", "column": "cogs", "invalid_condition": lambda s: s <= 0},
    {"table_name": "order_items", "column": "quantity", "invalid_condition": lambda s: s <= 0},
    {"table_name": "order_items", "column": "unit_price", "invalid_condition": lambda s: s <= 0},
    {"table_name": "order_items", "column": "discount_amount", "invalid_condition": lambda s: s < 0},
    {"table_name": "payments", "column": "payment_value", "invalid_condition": lambda s: s < 0},
    {"table_name": "shipments", "column": "shipping_fee", "invalid_condition": lambda s: s < 0},
    {"table_name": "returns", "column": "return_quantity", "invalid_condition": lambda s: s <= 0},
    {"table_name": "returns", "column": "refund_amount", "invalid_condition": lambda s: s < 0},
    {"table_name": "reviews", "column": "rating", "invalid_condition": lambda s: ~s.between(1, 5)},
    {"table_name": "sales", "column": "Revenue", "invalid_condition": lambda s: s <= 0},
    {"table_name": "sales", "column": "COGS", "invalid_condition": lambda s: s <= 0},
    {"table_name": "inventory", "column": "stock_on_hand", "invalid_condition": lambda s: s < 0},
    {"table_name": "inventory", "column": "units_sold", "invalid_condition": lambda s: s < 0},
    {"table_name": "inventory", "column": "fill_rate", "invalid_condition": lambda s: ~s.between(0, 1)},
    {"table_name": "inventory", "column": "sell_through_rate", "invalid_condition": lambda s: ~s.between(0, 1)},
    {"table_name": "web_traffic", "column": "sessions", "invalid_condition": lambda s: s < 0},
    {"table_name": "web_traffic", "column": "page_views", "invalid_condition": lambda s: s < 0},
    {"table_name": "web_traffic", "column": "bounce_rate", "invalid_condition": lambda s: ~s.between(0, 1)},
]


# --- From notebook cell 83 ---

def read_numeric_series(table_name: str, column: str) -> pd.Series:
    path = DATA_DIR / f"{table_name}.csv"
    if not path.exists() or path.stat().st_size == 0:
        return pd.Series(dtype="float64")
    df = pd.read_csv(path, usecols=[column], low_memory=False)
    return pd.to_numeric(df[column], errors="coerce")


def top_bottom_values(series: pd.Series, n: int = 5) -> tuple[str, str]:
    clean = series.dropna()
    bottom = clean.nsmallest(n).round(4).tolist()
    top = clean.nlargest(n).round(4).tolist()
    return str(bottom), str(top)


def outlier_decision(invalid_count: int, outlier_count: int) -> str:
    if invalid_count > 0:
        return "Fix/exclude"
    if outlier_count > 0:
        return "Flag only"
    return "Pass"


def outlier_note(invalid_count: int, outlier_count: int) -> str:
    if invalid_count > 0:
        return "Rule-based invalid values found; investigate before EDA."
    if outlier_count > 0:
        return "IQR extreme values found; flag for review but do not remove automatically."
    return "No invalid values or IQR outliers found."


def summarize_outlier_target(target: dict) -> dict:
    table_name = target["table_name"]
    column = target["column"]
    series = read_numeric_series(table_name, column)
    clean = series.dropna()

    if clean.empty:
        return {
            "table_name": table_name,
            "column": column,
            "method": "rule + IQR",
            "lower_bound": pd.NA,
            "upper_bound": pd.NA,
            "outlier_count": 0,
            "outlier_pct": 0.0,
            "min": pd.NA,
            "p1": pd.NA,
            "median": pd.NA,
            "p99": pd.NA,
            "max": pd.NA,
            "bottom_5": "[]",
            "top_5": "[]",
            "decision": "Investigate later",
            "note": "No numeric values available.",
        }

    invalid_mask = target["invalid_condition"](clean).fillna(False)
    invalid_count = int(invalid_mask.sum())

    q1 = clean.quantile(0.25)
    q3 = clean.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outlier_mask = (clean < lower_bound) | (clean > upper_bound)
    outlier_count = int(outlier_mask.sum())
    bottom_5, top_5 = top_bottom_values(clean)

    return {
        "table_name": table_name,
        "column": column,
        "method": "rule + IQR",
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outlier_count": outlier_count,
        "outlier_pct": round(outlier_count / max(len(clean), 1) * 100, 4),
        "min": clean.min(),
        "p1": clean.quantile(0.01),
        "median": clean.median(),
        "p99": clean.quantile(0.99),
        "max": clean.max(),
        "bottom_5": bottom_5,
        "top_5": top_5,
        "decision": outlier_decision(invalid_count, outlier_count),
        "note": outlier_note(invalid_count, outlier_count),
    }


def build_outlier_quality_summary(targets: list[dict]) -> pd.DataFrame:
    decision_order = {
        "Fix/exclude": 0,
        "Investigate later": 1,
        "Flag only": 2,
        "Pass": 3,
    }
    summary = pd.DataFrame([summarize_outlier_target(target) for target in targets])
    return (
        summary.assign(decision_rank=lambda df: df["decision"].map(decision_order).fillna(9))
        .sort_values(["decision_rank", "outlier_count", "table_name", "column"], ascending=[True, False, True, True])
        .drop(columns="decision_rank")
        .reset_index(drop=True)
    )


def plot_outlier_counts(summary: pd.DataFrame):
    plot_data = summary.query("outlier_count > 0").sort_values("outlier_count", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 6))
    if plot_data.empty:
        ax.text(0.5, 0.5, "No IQR outliers found", ha="center", va="center")
        ax.axis("off")
        return fig

    labels = plot_data["table_name"] + "." + plot_data["column"]
    ax.barh(labels, plot_data["outlier_count"], color="#F28E2B")
    clean_axis(ax, "IQR outlier count by column", xlabel="outlier rows")
    for index, row in enumerate(plot_data.itertuples()):
        ax.text(row.outlier_count * 1.01, index, f"{row.outlier_count:,}", va="center", fontsize=8)
    plt.tight_layout()


def plot_outlier_decisions(summary: pd.DataFrame):
    decision_order = ["Pass", "Flag only", "Investigate later", "Fix/exclude"]
    counts = summary["decision"].value_counts().reindex(decision_order).dropna()
    color_map = {
        "Pass": "#59A14F",
        "Flag only": "#F28E2B",
        "Investigate later": "#9D9D9D",
        "Fix/exclude": "#E15759",
    }
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(counts.index, counts.values, color=[color_map.get(value, "#9D9D9D") for value in counts.index])
    clean_axis(ax, "Outlier quality decisions", ylabel="columns")
    for index, value in enumerate(counts.values):
        ax.text(index, value + 0.05, int(value), ha="center", fontsize=9)
    plt.tight_layout()

def plot_numeric_distribution(table_name: str, column: str, bins: int = 40):
    series = read_numeric_series(table_name, column).dropna()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(series, bins=bins, color="#4E79A7", edgecolor="white")
    clean_axis(ax, f"Distribution: {table_name}.{column}", xlabel=column, ylabel="rows")
    plt.tight_layout()


def plot_sales_revenue_cogs_line():
    sales = pd.read_csv(DATA_DIR / "sales.csv", parse_dates=["Date"], low_memory=False)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(sales["Date"], sales["Revenue"], label="Revenue", color="#4E79A7", linewidth=1.2)
    ax.plot(sales["Date"], sales["COGS"], label="COGS", color="#E15759", linewidth=1.2)
    clean_axis(ax, "Sales Revenue and COGS over time", xlabel="date", ylabel="value")
    ax.legend(frameon=False)
    plt.tight_layout()


def build_payment_distribution_diagnostic() -> pd.DataFrame:
    payments = pd.read_csv(DATA_DIR / "payments.csv", low_memory=False)
    payment_value = payments["payment_value"]
    log_payment_value = np.log1p(payment_value)

    records = [
        {
            "metric": "payment_value",
            "rows": len(payment_value),
            "mean": payment_value.mean(),
            "median": payment_value.median(),
            "std": payment_value.std(),
            "skew": payment_value.skew(),
            "kurtosis": payment_value.kurtosis(),
            "min": payment_value.min(),
            "p1": payment_value.quantile(0.01),
            "p99": payment_value.quantile(0.99),
            "max": payment_value.max(),
            "note": "Right-skewed order-level value; not expected to be normal.",
        },
        {
            "metric": "log1p(payment_value)",
            "rows": len(log_payment_value),
            "mean": log_payment_value.mean(),
            "median": log_payment_value.median(),
            "std": log_payment_value.std(),
            "skew": log_payment_value.skew(),
            "kurtosis": log_payment_value.kurtosis(),
            "min": log_payment_value.min(),
            "p1": log_payment_value.quantile(0.01),
            "p99": log_payment_value.quantile(0.99),
            "max": log_payment_value.max(),
            "note": "Much closer to symmetric; payment values behave more like log-normal.",
        },
    ]
    return pd.DataFrame(records)


def build_payment_reconciliation_diagnostic() -> pd.DataFrame:
    order_items = pd.read_csv(
        DATA_DIR / "order_items.csv",
        usecols=["order_id", "quantity", "unit_price", "discount_amount"],
        low_memory=False,
    )
    payments = pd.read_csv(DATA_DIR / "payments.csv", usecols=["order_id", "payment_value"], low_memory=False)

    order_item_totals = (
        order_items.assign(
            gross_revenue=lambda df: df["quantity"] * df["unit_price"],
            net_revenue=lambda df: df["quantity"] * df["unit_price"] - df["discount_amount"],
        )
        .groupby("order_id", as_index=False)
        .agg(
            gross_revenue=("gross_revenue", "sum"),
            net_revenue=("net_revenue", "sum"),
            order_lines=("order_id", "size"),
            total_quantity=("quantity", "sum"),
        )
    )
    diagnostic = payments.merge(order_item_totals, on="order_id", how="left", validate="one_to_one")
    diagnostic["payment_minus_net"] = diagnostic["payment_value"] - diagnostic["net_revenue"]
    diagnostic["payment_minus_gross"] = diagnostic["payment_value"] - diagnostic["gross_revenue"]

    return pd.DataFrame(
        [
            {
                "check": "payment_value vs net_revenue",
                "affected_orders": int((diagnostic["payment_minus_net"].abs() > 0.01).sum()),
                "max_abs_diff": diagnostic["payment_minus_net"].abs().max(),
                "correlation": diagnostic["payment_value"].corr(diagnostic["net_revenue"]),
                "note": "payment_value exactly reconciles to sum(quantity * unit_price - discount_amount).",
            },
            {
                "check": "payment_value vs gross_revenue",
                "affected_orders": int((diagnostic["payment_minus_gross"].abs() > 0.01).sum()),
                "max_abs_diff": diagnostic["payment_minus_gross"].abs().max(),
                "correlation": diagnostic["payment_value"].corr(diagnostic["gross_revenue"]),
                "note": "difference is discount; payment_value is not gross order value.",
            },
        ]
    )


def build_payment_bucket_summary() -> pd.DataFrame:
    payments = pd.read_csv(DATA_DIR / "payments.csv", usecols=["payment_value"], low_memory=False)
    bins = [0, 1000, 5000, 10000, 20000, 50000, 100000, 200000, 400000]
    buckets = pd.cut(payments["payment_value"], bins=bins, right=False)
    counts = buckets.value_counts(sort=False)
    pct = buckets.value_counts(sort=False, normalize=True) * 100
    return pd.DataFrame(
        {
            "payment_bucket": counts.index.astype(str),
            "orders": counts.values,
            "order_pct": pct.values,
        }
    )


def plot_payment_distribution_diagnostic():
    payments = pd.read_csv(DATA_DIR / "payments.csv", usecols=["payment_value"], low_memory=False)
    payment_value = payments["payment_value"]
    log_payment_value = np.log1p(payment_value)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    axes[0].hist(payment_value, bins=60, color="#4E79A7", edgecolor="white")
    clean_axis(axes[0], "payment_value distribution", xlabel="payment_value", ylabel="orders")

    axes[1].hist(log_payment_value, bins=60, color="#59A14F", edgecolor="white")
    clean_axis(axes[1], "log1p(payment_value) distribution", xlabel="log1p(payment_value)", ylabel="orders")
    plt.tight_layout()


def plot_payment_bucket_summary(bucket_summary: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(bucket_summary["payment_bucket"], bucket_summary["orders"], color="#4E79A7")
    clean_axis(ax, "Payment value buckets", xlabel="payment_value bucket", ylabel="orders")
    ax.tick_params(axis="x", rotation=30)
    for index, row in enumerate(bucket_summary.itertuples(index=False)):
        ax.text(index, row.orders, f"{row.order_pct:.1f}%", ha="center", va="bottom", fontsize=8)
    plt.tight_layout()


def _append_issue(records: list[dict], source_check: str, table_name: str, column: str, issue_type: str, affected_rows, affected_pct, severity: str, decision: str, reason: str) -> None:
    try:
        affected_rows = int(affected_rows)
    except (TypeError, ValueError):
        affected_rows = 0
    try:
        affected_pct = float(affected_pct)
    except (TypeError, ValueError):
        affected_pct = 0.0
    records.append(
        {
            "source_check": source_check,
            "table_name": table_name,
            "column": column,
            "issue_type": issue_type,
            "affected_rows": affected_rows,
            "affected_pct": affected_pct,
            "severity": severity,
            "decision": decision,
            "reason": reason,
        }
    )


def build_data_quality_issue_log(
    dtype_issues: pd.DataFrame | None = None,
    missing_summary: pd.DataFrame | None = None,
    duplicate_key_summary: pd.DataFrame | None = None,
    relationship_checks: pd.DataFrame | None = None,
    time_logic_issues: pd.DataFrame | None = None,
    business_rule_issues: pd.DataFrame | None = None,
    order_lifecycle_issues: pd.DataFrame | None = None,
    sales_transaction_issues: pd.DataFrame | None = None,
    outlier_quality_summary: pd.DataFrame | None = None,
) -> pd.DataFrame:
    records = []

    if dtype_issues is not None and not dtype_issues.empty:
        for row in dtype_issues.itertuples(index=False):
            _append_issue(
                records,
                "dtype_issues",
                row.table_name,
                row.column_name,
                "dtype_or_domain_issue",
                0,
                0.0,
                row.severity,
                row.decision,
                row.issue,
            )

    if missing_summary is not None and not missing_summary.empty:
        for row in missing_summary.itertuples(index=False):
            interpretation = str(row.interpretation)
            severity = "Low" if interpretation.startswith("Business expected") else "High"
            decision = "Keep as is" if severity == "Low" else "Fix before EDA"
            _append_issue(
                records,
                "missing_summary",
                row.table_name,
                row.column,
                "missing_values",
                row.missing_count,
                row.missing_pct,
                severity,
                decision,
                f"{row.interpretation} Action: {row.action}",
            )

    if duplicate_key_summary is not None and not duplicate_key_summary.empty:
        for row in duplicate_key_summary.query("duplicate_rows > 0").itertuples(index=False):
            decision = "Fix before EDA" if row.severity == "High" else "Investigate later"
            _append_issue(
                records,
                "duplicate_key_summary",
                row.table_name,
                row.key_columns,
                "duplicate_key",
                row.duplicate_rows,
                row.duplicate_rows / max(row.rows, 1) * 100,
                row.severity,
                decision,
                row.note,
            )

    if relationship_checks is not None and not relationship_checks.empty:
        issue_rows = relationship_checks.query("orphan_rows > 0 or parent_duplicate_rows > 0")
        for row in issue_rows.itertuples(index=False):
            affected_rows = row.orphan_rows if row.orphan_rows > 0 else row.parent_duplicate_rows
            issue_type = "orphan_foreign_key" if row.orphan_rows > 0 else "duplicate_parent_key"
            _append_issue(
                records,
                "relationship_checks",
                row.child_table,
                row.child_key,
                issue_type,
                affected_rows,
                row.orphan_pct,
                row.severity,
                "Fix before EDA" if row.severity == "High" else "Investigate later",
                row.note,
            )

    if time_logic_issues is not None and not time_logic_issues.empty:
        for row in time_logic_issues.query("issue_count > 0").itertuples(index=False):
            _append_issue(
                records,
                "time_logic_issues",
                "multiple",
                "",
                row.rule,
                row.issue_count,
                row.issue_pct,
                row.severity,
                "Investigate later" if row.severity == "High" else "Flag only",
                "Temporal logic violation found. Review sample_rows in time_logic_issues.",
            )

    if business_rule_issues is not None and not business_rule_issues.empty:
        for row in business_rule_issues.query("issue_count > 0").itertuples(index=False):
            decision = "Fix before EDA" if row.severity == "High" else "Investigate later"
            _append_issue(
                records,
                "business_rule_issues",
                row.table_name,
                "",
                row.rule,
                row.issue_count,
                row.issue_pct,
                row.severity,
                decision,
                row.note,
            )

    if order_lifecycle_issues is not None and not order_lifecycle_issues.empty:
        for row in order_lifecycle_issues.query("issue_count > 0").itertuples(index=False):
            _append_issue(
                records,
                "order_lifecycle_issues",
                "orders",
                "order_status",
                row.rule,
                row.issue_count,
                row.issue_pct,
                row.severity,
                "Investigate later",
                row.note,
            )

    if sales_transaction_issues is not None and not sales_transaction_issues.empty:
        for row in sales_transaction_issues.query("severity != 'OK'").itertuples(index=False):
            _append_issue(
                records,
                "sales_transaction_issues",
                "sales",
                "",
                row.issue,
                row.affected_dates,
                0.0,
                row.severity,
                row.decision,
                row.reason,
            )

    if outlier_quality_summary is not None and not outlier_quality_summary.empty:
        for row in outlier_quality_summary.query("decision != 'Pass'").itertuples(index=False):
            severity = "High" if row.decision == "Fix/exclude" else "Low"
            _append_issue(
                records,
                "outlier_quality_summary",
                row.table_name,
                row.column,
                "iqr_outlier_or_invalid_value",
                row.outlier_count,
                row.outlier_pct,
                severity,
                row.decision,
                row.note,
            )

    columns = [
        "issue_id",
        "source_check",
        "table_name",
        "column",
        "issue_type",
        "affected_rows",
        "affected_pct",
        "severity",
        "decision",
        "reason",
    ]
    if not records:
        return pd.DataFrame(columns=columns)

    severity_order = {"High": 0, "Medium": 1, "Low": 2, "OK": 3}
    issue_log = (
        pd.DataFrame(records)
        .assign(severity_rank=lambda df: df["severity"].map(severity_order).fillna(9))
        .sort_values(["severity_rank", "affected_rows", "source_check"], ascending=[True, False, True])
        .drop(columns="severity_rank")
        .reset_index(drop=True)
    )
    issue_log.insert(0, "issue_id", [f"DQ-{index + 1:03d}" for index in range(len(issue_log))])
    return issue_log[columns]


def plot_issue_log_severity(issue_log: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    if issue_log.empty:
        ax.text(0.5, 0.5, "No data quality issues logged", ha="center", va="center")
        ax.axis("off")
        return
    counts = issue_log["severity"].value_counts().reindex(["High", "Medium", "Low"]).dropna()
    color_map = {"High": "#E15759", "Medium": "#F28E2B", "Low": "#76B7B2"}
    ax.bar(counts.index, counts.values, color=[color_map.get(value, "#9D9D9D") for value in counts.index])
    clean_axis(ax, "Data quality issue log by severity", ylabel="issues")
    for index, value in enumerate(counts.values):
        ax.text(index, value + 0.05, int(value), ha="center", fontsize=9)
    plt.tight_layout()


def plot_issue_log_sources(issue_log: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 4))
    if issue_log.empty:
        ax.text(0.5, 0.5, "No data quality issues logged", ha="center", va="center")
        ax.axis("off")
        return
    counts = issue_log["source_check"].value_counts().sort_values()
    ax.barh(counts.index, counts.values, color="#4E79A7")
    clean_axis(ax, "Data quality issues by source check", xlabel="issues")
    for index, value in enumerate(counts.values):
        ax.text(value + 0.05, index, int(value), va="center", fontsize=9)
    plt.tight_layout()
