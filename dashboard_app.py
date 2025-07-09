# app.py
# ──────────────────────────────────────────
# 📊 販売データBIダッシュボード
# ──────────────────────────────────────────
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

# ─────────────────────────────
# データ読み込み（キャッシュ）
# ─────────────────────────────
@st.cache_data
def load_data(csv_path: str) -> pd.DataFrame:
    """CSV を読み込み、date 列を datetime へ変換して返す"""
    return pd.read_csv(csv_path, parse_dates=["date"])

DATA_PATH = "data/sample_sales.csv"
df = load_data(DATA_PATH)

# ─────────────────────────────
# UI ― サイドバー（フィルター類）
# ─────────────────────────────
st.sidebar.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=180)
st.sidebar.markdown("### 販売ダッシュボード")
st.sidebar.info("期間やカテゴリで売上データを分析できます。")

st.sidebar.header("📅 期間フィルター")

min_date = df["date"].min().to_pydatetime()
max_date = df["date"].max().to_pydatetime()

# 期間選択：デフォルトは全期間
date_range = st.sidebar.date_input(
    label="表示期間を選択",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="YYYY-MM-DD",
)

# date_input はタプルもしくは単一日付を返す
if isinstance(date_range, tuple):
    date_start, date_end = date_range
else:
    date_start = date_end = date_range

# ─────────────────────────────
# データフィルタリング
# ─────────────────────────────
mask = (df["date"] >= pd.to_datetime(date_start)) & (df["date"] <= pd.to_datetime(date_end))
filtered_df = df.loc[mask]

# ─────────────────────────────
# ページタイトル & KPI 指標
# ─────────────────────────────
st.title("📊 販売データBIダッシュボード")
st.write(f"集計対象期間: **{date_start.strftime('%Y-%m-%d')}～{date_end.strftime('%Y-%m-%d')}**")

total_revenue = int(filtered_df["revenue"].sum())
total_units = int(filtered_df["units"].sum())
category_count = filtered_df["category"].nunique()

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric("💰 売上合計", f"{total_revenue:,.0f} 円")
with kpi2:
    st.metric("📦 販売数量合計", f"{total_units:,} 個")
with kpi3:
    st.metric("🗂️ 商品カテゴリ数", f"{category_count:,} 種類")

# ─────────────────────────────
# グラフ ①：カテゴリ別売上（棒グラフ）
# ─────────────────────────────
st.subheader("カテゴリ別売上（棒グラフ）")
rev_by_cat = (
    filtered_df.groupby("category", as_index=False)["revenue"]
    .sum()
    .sort_values("revenue", ascending=False)
)

bar_fig = px.bar(
    rev_by_cat,
    x="category",
    y="revenue",
    labels={"category": "カテゴリ", "revenue": "売上 (円)"},
    text="revenue",
    color="revenue",
    color_continuous_scale="Blues",
)
bar_fig.update_traces(texttemplate="%{text:,.0f} 円", textposition="outside")
bar_fig.update_layout(xaxis_tickangle=-45, yaxis_tickformat=",", showlegend=False)

st.plotly_chart(bar_fig, use_container_width=True)

# ─────────────────────────────
# グラフ ②：日毎の売上推移（折れ線グラフ）
# ─────────────────────────────
st.subheader("日毎の売上推移（折れ線グラフ）")
daily_rev = (
    filtered_df.groupby("date", as_index=False)["revenue"]
    .sum()
    .sort_values("date")
)

line_fig = px.line(
    daily_rev,
    x="date",
    y="revenue",
    markers=True,
    labels={"date": "日付", "revenue": "売上 (円)"},
    line_shape="spline",
)
line_fig.update_layout(yaxis_tickformat=",", xaxis_title="日付", yaxis_title="売上 (円)")

st.plotly_chart(line_fig, use_container_width=True)

# ─────────────────────────────
# データダウンロード
# ─────────────────────────────
st.download_button(
    label="📥 フィルタ済みデータをCSVでダウンロード",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_sales.csv",
    mime="text/csv",
)

# ─────────────────────────────
# フッター
# ─────────────────────────────
st.caption("© 2025 BI Dashboard with Streamlit")
