import io
import pandas as pd
import streamlit as st

st.title("📄 Pandas Basics ‒ Sample Sales CSV")

# ① CSV を読み込む
df = pd.read_csv("data/sample_sales.csv", parse_dates=["date"])

# ② 中身をのぞく
st.subheader("① Data Preview (head)")
st.dataframe(df.head(), use_container_width=True)

st.subheader("② DataFrame info()")
buf = io.StringIO()
df.info(buf=buf)
st.text(buf.getvalue())

st.subheader("③ describe() (numeric summary)")
st.dataframe(df.describe(), use_container_width=True)

# ③ 基本集計：カテゴリ別 売上合計
st.subheader("④ Total Revenue by Category")
rev_by_cat = (
    df.groupby("category")["revenue"]
      .sum()
      .sort_values(ascending=False)
)

st.write(rev_by_cat)      # 表示だけで OK
# もしグラフにしたい場合は ↓ をアンコメント
# st.bar_chart(rev_by_cat)
