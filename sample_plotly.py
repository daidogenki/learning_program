import streamlit as st
import pandas as pd
import plotly.express as px

# ─────────────────────────────
# アプリのタイトルと説明
# ─────────────────────────────
st.title("Plotly基礎")
st.write("Plotlyを使ってインタラクティブなグラフを作成してみましょう！")

# ─────────────────────────────
# データ読み込み
# ─────────────────────────────
# 'date' 列が文字列の場合に備え parse_dates で読み込む
df = pd.read_csv("data/sample_sales.csv", parse_dates=["date"])

st.subheader("日別売上推移")

# ─────────────────────────────
# 日別合計売上を計算
# ─────────────────────────────
daily_revenue = (
    df.groupby(df["date"].dt.date)["revenue"]
    .sum()
    .reset_index()
    .rename(columns={"date": "Date", "revenue": "Revenue"})
)

# ─────────────────────────────
# 折れ線グラフを作成（線色は赤）
# ─────────────────────────────
fig = px.line(
    daily_revenue,
    x="Date",
    y="Revenue",
    title="日別売上推移",
    labels={"Date": "日付", "Revenue": "売上合計 (円)"},
)

fig.update_traces(line_color="red")  # 線を赤色に変更

# ─────────────────────────────
# グラフを表示
# ─────────────────────────────
st.plotly_chart(fig, use_container_width=True)

st.write("---")
st.write("このグラフはインタラクティブです！線上にカーソルを合わせると、その日の正確な売上が表示されます。")
