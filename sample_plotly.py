import streamlit as st
import pandas as pd
import plotly.express as px

# ─────────────────────────────
# アプリのタイトルと説明
# ─────────────────────────────
st.title("Plotly基礎")
st.write("Plotlyを使ってインタラクティブなグラフを作成してみましょう！")

# ─────────────────────────────
# CSVファイルを読み込む
# ─────────────────────────────
df = pd.read_csv("data/sample_sales.csv")

# ① 日付列を datetime 型に変換
df["date"] = pd.to_datetime(df["date"])

st.subheader("日別売上推移（折れ線グラフ）")

# ② 日毎の売上を集計
daily_revenue = (
    df.groupby("date")["revenue"]
      .sum()
      .reset_index()
      .sort_values("date")           # 日付順に並べ替え（任意）
)

# ③ Plotly で折れ線グラフを作成
fig = px.line(
    daily_revenue,
    x="date",
    y="revenue",
    title="日別売上推移",
    labels={"date": "日付", "revenue": "売上 (円)"},
)

# ④ 線の色を赤に変更
fig.update_traces(line_color="red")

# ⑤ Streamlit にグラフを表示
st.plotly_chart(fig, use_container_width=True)

st.write("---")
st.write("このグラフはインタラクティブです！範囲選択やズームで詳細を確認できます。")
