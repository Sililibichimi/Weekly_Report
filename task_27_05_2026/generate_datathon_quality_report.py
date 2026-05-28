from __future__ import annotations

import base64
import html
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from datathon_quality import *


REPORT_PATH = Path(__file__).with_name("datathon_data_quality_report.html")


def pct(value: float | int | None, digits: int = 2) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.{digits}f}%"


def num(value: float | int | None, digits: int = 2) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.{digits}f}"
    return f"{int(value):,}"


def date_text(value) -> str:
    if pd.isna(value):
        return ""
    return pd.to_datetime(value).strftime("%Y-%m-%d")


def clean_table(df: pd.DataFrame, max_rows: int | None = None) -> pd.DataFrame:
    out = df.copy()
    if max_rows is not None:
        out = out.head(max_rows).copy()
    for column in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[column]):
            out[column] = out[column].dt.strftime("%Y-%m-%d")
    return out


def table_html(df: pd.DataFrame, max_rows: int | None = None, index: bool = False) -> str:
    if df is None or df.empty:
        return '<p class="muted">Không có bản ghi.</p>'
    out = clean_table(df, max_rows=max_rows)
    return out.to_html(index=index, escape=True, classes="data-table", border=0)


def figure_html(title: str, plot_func, *args, **kwargs) -> str:
    plt.close("all")
    result = plot_func(*args, **kwargs)
    fig = result if result is not None else plt.gcf()
    if fig is None or not fig.axes:
        return ""

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    safe_title = html.escape(title)
    return (
        f'<figure class="chart">'
        f'<figcaption>{safe_title}</figcaption>'
        f'<img alt="{safe_title}" src="data:image/png;base64,{encoded}">'
        f"</figure>"
    )


def metric_card(label: str, value: str, note: str = "") -> str:
    return (
        '<div class="metric">'
        f'<div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value">{html.escape(value)}</div>'
        f'<div class="metric-note">{html.escape(note)}</div>'
        "</div>"
    )


def section(title: str, body: str) -> str:
    return f'<section><h2>{html.escape(title)}</h2>{body}</section>'


def subsection(title: str, body: str) -> str:
    return f'<h3>{html.escape(title)}</h3>{body}'


def severity_summary(issue_log: pd.DataFrame) -> pd.DataFrame:
    order = ["High", "Medium", "Low"]
    counts = issue_log["severity"].value_counts().reindex(order, fill_value=0)
    return counts.rename_axis("severity").reset_index(name="issues")


def source_summary(issue_log: pd.DataFrame) -> pd.DataFrame:
    return (
        issue_log.groupby("source_check", dropna=False)
        .agg(issues=("issue_id", "count"), affected_rows=("affected_rows", "sum"))
        .sort_values(["issues", "affected_rows"], ascending=False)
        .reset_index()
    )


def build_results() -> dict[str, pd.DataFrame | dict]:
    files = sorted(DATA_DIR.glob("*.csv"))
    file_inventory_df = build_file_inventory(files, TABLE_INFO)
    date_meta_df = build_date_meta(files)
    table_overview = build_table_overview(file_inventory_df, date_meta_df)
    overview_decision_matrix = build_decision_matrix(file_inventory_df)
    plot_df = build_plot_df(file_inventory_df, date_meta_df)

    column_profile_summary = build_column_profile_summary(files)
    table_type_summary = build_table_type_summary(column_profile_summary)
    category_domain_summary = build_category_domain_summary(column_profile_summary, files)
    numeric_profile_summary = build_numeric_profile_summary(column_profile_summary, files)
    date_parse_summary = build_date_parse_summary(column_profile_summary, files)
    dtype_issues = build_dtype_issues(column_profile_summary, files)

    missing_profile = build_missing_profile(files)
    missing_summary = build_missing_summary(files, only_missing=True)

    date_range_summary = build_date_range_summary(DATE_RANGE_CHECKS)
    time_logic_issues = build_time_logic_issues()
    date_continuity_summary = build_date_continuity_summary(date_range_summary)
    forecast_availability = build_forecast_availability_table()

    duplicate_key_summary = build_duplicate_key_summary(PRIMARY_KEY_CHECKS, CANDIDATE_KEY_CHECKS)
    relationship_checks = build_relationship_checks(RELATIONSHIPS)

    business_rule_issues = build_business_rule_issues(BUSINESS_RULES)

    order_lifecycle = build_order_lifecycle_table()
    order_status_summary = build_order_status_summary(order_lifecycle)
    payment_order_check = build_payment_order_check()
    lifecycle_consistency_issues = build_lifecycle_consistency_issues(order_lifecycle)

    sales_transaction_consistency, sales_transaction_daily = build_sales_transaction_consistency()
    sales_transaction_issues = build_sales_transaction_issues(
        sales_transaction_consistency,
        sales_transaction_daily,
    )

    outlier_quality_summary = build_outlier_quality_summary(OUTLIER_TARGETS)
    payment_distribution_diagnostic = build_payment_distribution_diagnostic()
    payment_reconciliation_diagnostic = build_payment_reconciliation_diagnostic()
    payment_bucket_summary = build_payment_bucket_summary()

    data_quality_issue_log = build_data_quality_issue_log(
        dtype_issues=dtype_issues,
        missing_summary=missing_summary,
        duplicate_key_summary=duplicate_key_summary,
        relationship_checks=relationship_checks,
        time_logic_issues=time_logic_issues,
        business_rule_issues=business_rule_issues,
        order_lifecycle_issues=lifecycle_consistency_issues,
        sales_transaction_issues=sales_transaction_issues,
        outlier_quality_summary=outlier_quality_summary,
    )

    return locals()


def render_report(results: dict[str, pd.DataFrame | dict]) -> str:
    file_inventory_df = results["file_inventory_df"]
    table_overview = results["table_overview"]
    overview_decision_matrix = results["overview_decision_matrix"]
    plot_df = results["plot_df"]
    column_profile_summary = results["column_profile_summary"]
    table_type_summary = results["table_type_summary"]
    category_domain_summary = results["category_domain_summary"]
    numeric_profile_summary = results["numeric_profile_summary"]
    date_parse_summary = results["date_parse_summary"]
    dtype_issues = results["dtype_issues"]
    missing_summary = results["missing_summary"]
    date_range_summary = results["date_range_summary"]
    time_logic_issues = results["time_logic_issues"]
    date_continuity_summary = results["date_continuity_summary"]
    forecast_availability = results["forecast_availability"]
    duplicate_key_summary = results["duplicate_key_summary"]
    relationship_checks = results["relationship_checks"]
    business_rule_issues = results["business_rule_issues"]
    order_status_summary = results["order_status_summary"]
    payment_order_check = results["payment_order_check"]
    lifecycle_consistency_issues = results["lifecycle_consistency_issues"]
    sales_transaction_consistency = results["sales_transaction_consistency"]
    sales_transaction_daily = results["sales_transaction_daily"]
    sales_transaction_issues = results["sales_transaction_issues"]
    outlier_quality_summary = results["outlier_quality_summary"]
    payment_distribution_diagnostic = results["payment_distribution_diagnostic"]
    payment_reconciliation_diagnostic = results["payment_reconciliation_diagnostic"]
    payment_bucket_summary = results["payment_bucket_summary"]
    data_quality_issue_log = results["data_quality_issue_log"]

    issue_counts = severity_summary(data_quality_issue_log)
    high_issues = int(issue_counts.loc[issue_counts["severity"] == "High", "issues"].iloc[0])
    medium_issues = int(issue_counts.loc[issue_counts["severity"] == "Medium", "issues"].iloc[0])
    low_issues = int(issue_counts.loc[issue_counts["severity"] == "Low", "issues"].iloc[0])
    csv_count = len(file_inventory_df)
    total_rows = int(file_inventory_df["rows"].sum())
    relationship_non_ok = int((relationship_checks["severity"] != "OK").sum())
    duplicate_with_issues = int((duplicate_key_summary["duplicate_rows"] > 0).sum())
    time_issue_rules = int((time_logic_issues["issue_count"] > 0).sum())
    business_issue_rules = int((business_rule_issues["issue_count"] > 0).sum())

    critical_issue_log = data_quality_issue_log.query("severity in ['High', 'Medium']").copy()
    issue_by_source = source_summary(data_quality_issue_log)
    non_ok_relationships = relationship_checks.query("severity != 'OK'").copy()
    if non_ok_relationships.empty:
        relationship_note = '<p class="good">Không phát hiện orphan key hoặc duplicate parent key trong 14 relationship được kiểm tra.</p>'
    else:
        relationship_note = table_html(non_ok_relationships)

    best_revenue = (
        sales_transaction_consistency.query("compared_metric.str.contains('Revenue', na=False)", engine="python")
        .sort_values(["MAE", "median_AE"])
        .head(5)
    )
    best_cogs = (
        sales_transaction_consistency.query("compared_metric.str.contains('COGS', na=False)", engine="python")
        .sort_values(["MAE", "median_AE"])
        .head(5)
    )

    missing_top = missing_summary.sort_values("missing_count", ascending=False).head(12)
    business_top = business_rule_issues.query("issue_count > 0").head(20)
    lifecycle_top = lifecycle_consistency_issues.query("issue_count > 0").head(20)
    outlier_top = outlier_quality_summary.query("decision != 'Pass'").head(25)

    cards = "".join(
        [
            metric_card("CSV tables", num(csv_count), f"{num(total_rows)} total rows"),
            metric_card("DQ issues", num(len(data_quality_issue_log)), f"High {high_issues}, Medium {medium_issues}, Low {low_issues}"),
            metric_card("Relationship issues", num(relationship_non_ok), "14 relationships checked"),
            metric_card("Duplicate key checks", num(duplicate_with_issues), "tables/keys with duplicate rows"),
            metric_card("Time logic rules with issues", num(time_issue_rules), "equality dates are treated as valid"),
            metric_card("Business rules with issues", num(business_issue_rules), "rule-based violations"),
        ]
    )

    executive_body = f"""
    <div class="metrics">{cards}</div>
    <div class="callout">
      <strong>Kết luận ngắn:</strong> Bộ kiểm tra data quality đã bao phủ schema, missing, date/time,
      duplicate/primary key, relationship, business rules, order lifecycle, sales-vs-transaction,
      outlier và issue log cuối. Relationship checks đang sạch; các điểm cần ưu tiên nằm ở time logic,
      order lifecycle, một số duplicate key, sales/profit consistency và outlier cần flag.
    </div>
    {subsection("Issue log ưu tiên", table_html(critical_issue_log))}
    {subsection("Issue theo nguồn kiểm tra", table_html(issue_by_source))}
    {figure_html("Issue log by severity", plot_issue_log_severity, data_quality_issue_log)}
    {figure_html("Issue log by source", plot_issue_log_sources, data_quality_issue_log)}
    """

    overview_body = f"""
    {table_html(table_overview)}
    <div class="chart-grid">
      {figure_html("Rows by table", plot_rows_by_table, plot_df)}
      {figure_html("Date coverage", plot_date_coverage, plot_df)}
      {figure_html("Rows vs columns", plot_rows_vs_columns, plot_df)}
    </div>
    {subsection("Decision matrix", table_html(overview_decision_matrix))}
    """

    schema_body = f"""
    {subsection("Table type summary", table_html(table_type_summary))}
    <div class="chart-grid">
      {figure_html("Schema overview", plot_appendix_schema_overview, column_profile_summary)}
      {figure_html("Dtype/domain issues", plot_schema_dtype_issues, dtype_issues)}
    </div>
    {subsection("Dtype issues", table_html(dtype_issues))}
    {subsection("Date parsing summary", table_html(date_parse_summary))}
    {subsection("Numeric profile summary", table_html(numeric_profile_summary, max_rows=30))}
    {subsection("Categorical domain checks", table_html(category_domain_summary, max_rows=30))}
    """

    missing_body = f"""
    {subsection("Missing summary", table_html(missing_top))}
    <div class="chart-grid">
      {figure_html("Top missing columns", plot_missing_columns, missing_summary)}
      {figure_html("Missing values by interpretation", plot_missing_interpretation, missing_summary)}
    </div>
    """

    date_body = f"""
    {subsection("Date range summary", table_html(date_range_summary))}
    {subsection("Date continuity summary", table_html(date_continuity_summary))}
    {subsection("Time logic issues", table_html(time_logic_issues))}
    {subsection("Forecast availability / leakage note", table_html(forecast_availability))}
    <div class="chart-grid">
      {figure_html("Date ranges", plot_date_ranges, date_range_summary)}
      {figure_html("Time logic issue counts", plot_time_logic_issues, time_logic_issues)}
    </div>
    <p class="note">Ghi chú: rule <code>signup_date &lt;= order_date</code> coi trường hợp đăng ký và mua hàng cùng ngày là hợp lệ; chỉ flag khi <code>signup_date &gt; order_date</code>.</p>
    """

    key_body = f"""
    {subsection("Duplicate key summary", table_html(duplicate_key_summary))}
    <div class="chart-grid">
      {figure_html("Duplicate rows by key", plot_duplicate_rows, duplicate_key_summary)}
      {figure_html("Duplicate severity", plot_duplicate_severity, duplicate_key_summary)}
    </div>
    {subsection("Relationship checks", table_html(relationship_checks))}
    {relationship_note}
    <div class="chart-grid">
      {figure_html("Relationship orphan rows", plot_relationship_orphans, relationship_checks)}
      {figure_html("Relationship status", plot_relationship_status, relationship_checks)}
    </div>
    """

    business_body = f"""
    {table_html(business_top)}
    <div class="chart-grid">
      {figure_html("Business rule issue counts", plot_business_rule_issues, business_rule_issues)}
      {figure_html("Business rule severity", plot_business_rule_severity, business_rule_issues)}
    </div>
    """

    lifecycle_body = f"""
    {subsection("Order status summary", table_html(order_status_summary))}
    {subsection("Payment vs orders check", table_html(payment_order_check))}
    {subsection("Lifecycle consistency issues", table_html(lifecycle_top))}
    <div class="chart-grid">
      {figure_html("Order status distribution", plot_order_status_distribution, order_status_summary)}
      {figure_html("Lifecycle issue counts", plot_lifecycle_issue_counts, lifecycle_consistency_issues)}
    </div>
    """

    sales_body = f"""
    {subsection("Best Revenue matches", table_html(best_revenue))}
    {subsection("Best COGS matches", table_html(best_cogs))}
    {subsection("Full consistency table", table_html(sales_transaction_consistency))}
    {subsection("Sales transaction issues", table_html(sales_transaction_issues))}
    <div class="chart-grid">
      {figure_html("Sales transaction MAE", plot_sales_transaction_mae, sales_transaction_consistency)}
      {figure_html("Sales vs gross revenue", plot_sales_vs_gross_revenue, sales_transaction_daily)}
    </div>
    """

    outlier_body = f"""
    {subsection("Outlier quality summary", table_html(outlier_top))}
    <div class="chart-grid">
      {figure_html("Outlier counts", plot_outlier_counts, outlier_quality_summary)}
      {figure_html("Outlier decisions", plot_outlier_decisions, outlier_quality_summary)}
      {figure_html("Sales Revenue and COGS over time", plot_sales_revenue_cogs_line)}
    </div>
    {subsection("Payment distribution diagnostic", table_html(payment_distribution_diagnostic))}
    {subsection("Payment reconciliation diagnostic", table_html(payment_reconciliation_diagnostic))}
    {subsection("Payment bucket summary", table_html(payment_bucket_summary))}
    <div class="chart-grid">
      {figure_html("Payment value distribution", plot_payment_distribution_diagnostic)}
      {figure_html("Payment bucket summary", plot_payment_bucket_summary, payment_bucket_summary)}
    </div>
    <p class="note">Payment thường lệch phải trong dữ liệu đơn hàng/bán lẻ vì nhiều đơn giá trị thấp và ít đơn giá trị cao; không cần giả định phân phối chuẩn.</p>
    """

    issue_body = f"""
    {table_html(data_quality_issue_log)}
    """

    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    html_body = "\n".join(
        [
            section("Executive summary", executive_body),
            section("1. Tổng quan bảng", overview_body),
            section("1B. Schema và column profiling", schema_body),
            section("2. Missing values", missing_body),
            section("3. Date range và time consistency", date_body),
            section("4. Duplicate key và relationships", key_body),
            section("5. Business rules", business_body),
            section("6. Order lifecycle và status consistency", lifecycle_body),
            section("7. Sales vs transaction consistency", sales_body),
            section("8. Outlier checks", outlier_body),
            section("9. Data quality issue log", issue_body),
        ]
    )

    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Datathon Data Quality Report</title>
  <style>
    :root {{
      --ink: #17202a;
      --muted: #667085;
      --line: #d9dee7;
      --panel: #f7f9fc;
      --accent: #2f6f9f;
      --good: #237a57;
      --warn: #a66300;
      --bad: #b42318;
    }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
      background: #ffffff;
      line-height: 1.45;
    }}
    header {{
      padding: 32px 40px 22px;
      border-bottom: 1px solid var(--line);
      background: #eef4f8;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px 28px 48px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 30px;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 36px 0 14px;
      padding-bottom: 8px;
      border-bottom: 2px solid var(--line);
      font-size: 22px;
    }}
    h3 {{
      margin: 22px 0 10px;
      font-size: 16px;
    }}
    .subtitle, .muted, .note {{
      color: var(--muted);
    }}
    .note {{
      font-size: 14px;
    }}
    .callout {{
      margin: 18px 0;
      padding: 14px 16px;
      border-left: 4px solid var(--accent);
      background: var(--panel);
    }}
    .good {{
      padding: 12px 14px;
      color: var(--good);
      background: #eff8f3;
      border: 1px solid #cbe9d8;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin: 16px 0;
    }}
    .metric {{
      padding: 14px 16px;
      border: 1px solid var(--line);
      background: #fff;
    }}
    .metric-label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .04em;
    }}
    .metric-value {{
      margin-top: 4px;
      font-size: 26px;
      font-weight: 700;
    }}
    .metric-note {{
      margin-top: 3px;
      color: var(--muted);
      font-size: 13px;
    }}
    .chart-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 18px;
      align-items: start;
    }}
    .chart {{
      margin: 12px 0;
      padding: 10px;
      border: 1px solid var(--line);
      background: #fff;
    }}
    .chart figcaption {{
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }}
    .chart img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      margin: 8px 0 18px;
      font-size: 13px;
    }}
    .data-table th {{
      position: sticky;
      top: 0;
      background: #f0f3f7;
      border: 1px solid var(--line);
      padding: 7px 8px;
      text-align: left;
      vertical-align: top;
    }}
    .data-table td {{
      border: 1px solid var(--line);
      padding: 6px 8px;
      vertical-align: top;
    }}
    .data-table tr:nth-child(even) td {{
      background: #fbfcfe;
    }}
    code {{
      background: #f1f3f5;
      padding: 1px 4px;
      border-radius: 3px;
    }}
    @media print {{
      header {{ background: #fff; }}
      .chart, .metric {{ break-inside: avoid; }}
      h2 {{ break-after: avoid; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Datathon Data Quality Report</h1>
    <div class="subtitle">Generated at {html.escape(generated_at)} | Data folder: {html.escape(str(DATA_DIR))}</div>
  </header>
  <main>
    {html_body}
  </main>
</body>
</html>
"""


def main() -> None:
    results = build_results()
    REPORT_PATH.write_text(render_report(results), encoding="utf-8")
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
