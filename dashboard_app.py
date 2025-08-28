"""
販売データBIダッシュボード
---------------------------
- data/sample_sales.csv を読み込み
- KPI（売上合計・販売数量合計・商品カテゴリ数）
- カテゴリ別売上棒グラフ
- 日別売上推移折れ線グラフ（赤色）
"""

# ──────────────────
# インポート
# ──────────────────
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ──────────────────
# データ読み込み関数
# ──────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    """
    CSV を読み込んで前処理を行う。
    - date 列を datetime 型に変換
    - 日付で昇順ソート
    """
    df = pd.read_csv(
        Path("data/sample_sales.csv"),
        parse_dates=["date"],
        dtype={
            "category": "string",
            "units": "int",
            "unit_price": "int",
            "region": "string",
            "sales_channel": "string",
            "customer_segment": "string",
            "revenue": "int",
        },
    ).sort_values("date")

    # 欠損値チェック（必要に応じて補完）
    if df.isna().any().any():
        st.warning("欠損値が含まれています。空セルを 0 で補完しました。")
        df = df.fillna(0)

    # revenue 一貫性チェック
    inconsistent = df[df["revenue"] != df["units"] * df["unit_price"]]
    if not inconsistent.empty:
        st.info(f"売上金額が一致しない行が {len(inconsistent)} 件あります。CSV の値を優先します。")

    return df


# ──────────────────
# メインアプリ
# ──────────────────
def main() -> None:
    st.set_page_config(page_title="販売データBIダッシュボード", layout="wide")
    st.title("📊 販売データBIダッシュボード")

    df = load_data()

    # ──────────────────
    # サイドバー ― フィルタ
    # ──────────────────
    st.sidebar.header("🔍 フィルタ")
    min_date, max_date = df["date"].min(), df["date"].max()

    date_range = st.sidebar.date_input(
        "期間を選択",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD",
    )

    # 日付範囲を DataFrame に適用
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    mask = (df["date"] >= start_date) & (df["date"] <= end_date)
    df_filtered = df.loc[mask]

    # ──────────────────
    # KPI カード
    # ──────────────────
    total_revenue = int(df_filtered["revenue"].sum())
    total_units = int(df_filtered["units"].sum())
    num_categories = df_filtered["category"].nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("売上合計 (円)", f"{total_revenue:,}")
    col2.metric("販売数量合計 (個)", f"{total_units:,}")
    col3.metric("商品カテゴリ数", num_categories)

    st.markdown("---")

    # ──────────────────
    # カテゴリ別売上棒グラフ
    # ──────────────────
    st.subheader("カテゴリ別売上")
    category_revenue = (
        df_filtered.groupby("category", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
    )

    fig_bar = px.bar(
        category_revenue,
        x="category",
        y="revenue",
        labels={"category": "商品カテゴリ", "revenue": "売上 (円)"},
        title="商品カテゴリごとの総売上",
    )
    fig_bar.update_layout(font_family="sans-serif", yaxis_tickformat=",")
    st.plotly_chart(fig_bar, use_container_width=True)

    # ──────────────────
    # 日別売上推移折れ線グラフ
    # ──────────────────
    st.subheader("日別売上推移")
    daily_revenue = (
        df_filtered.groupby("date", as_index=False)["revenue"].sum().sort_values("date")
    )

    fig_line = px.line(
        daily_revenue,
        x="date",
        y="revenue",
        labels={"date": "日付", "revenue": "売上 (円)"},
        title="日毎の売上推移",
    )
    fig_line.update_traces(line_color="red")
    fig_line.update_layout(font_family="sans-serif", yaxis_tickformat=",")
    st.plotly_chart(fig_line, use_container_width=True)


if __name__ == "__main__":
    main()
