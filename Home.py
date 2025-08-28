import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

st.set_page_config(page_title="Streamlit BI x Claude Code Starter", layout="wide")

st.title("Streamlit BI x Claude Code Starter")
@st.cache_data
def load_data():
    try:
        orders_df = pd.read_csv("sample_data/orders.csv")
        users_df = pd.read_csv("sample_data/users.csv")
        
        # データ前処理
        orders_df['created_at'] = pd.to_datetime(orders_df['created_at'], errors='coerce')
        orders_df = orders_df.dropna(subset=['created_at'])
        orders_df['year_month'] = orders_df['created_at'].dt.to_period('M').astype(str)
        
        return orders_df, users_df
    except FileNotFoundError:
        st.error("データファイルが見つかりません")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data
def prepare_monthly_analysis(orders_df):
    if orders_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    try:
        # 月別総注文数
        monthly_orders = orders_df.groupby('year_month').size().reset_index(name='total_orders')
        
        # 月別キャンセル数
        monthly_cancelled = orders_df[orders_df['status'] == 'Cancelled'].groupby('year_month').size().reset_index(name='cancelled_orders')
        
        # データ結合
        monthly_data = monthly_orders.merge(monthly_cancelled, on='year_month', how='left')
        monthly_data['cancelled_orders'] = monthly_data['cancelled_orders'].fillna(0)
        
        # キャンセル率計算
        monthly_data['cancel_rate'] = (monthly_data['cancelled_orders'] / monthly_data['total_orders'] * 100).round(2)
        
        return monthly_data, orders_df
    except Exception as e:
        st.error(f"月別分析データ準備エラー: {e}")
        return pd.DataFrame(), pd.DataFrame()

orders_df, users_df = load_data()

# 月別分析セクション
st.header("📈 月別オーダー分析")

if not orders_df.empty:
    monthly_data, _ = prepare_monthly_analysis(orders_df)
    
    if not monthly_data.empty:
        # サマリー指標
        col1, col2, col3 = st.columns(3)
        with col1:
            total_orders = monthly_data['total_orders'].sum()
            st.metric("総注文数", f"{total_orders:,}")
        with col2:
            avg_cancel_rate = monthly_data['cancel_rate'].mean()
            st.metric("平均キャンセル率", f"{avg_cancel_rate:.1f}%")
        with col3:
            max_cancel_rate = monthly_data['cancel_rate'].max()
            max_month = monthly_data[monthly_data['cancel_rate'] == max_cancel_rate]['year_month'].iloc[0]
            st.metric("最高キャンセル率", f"{max_cancel_rate:.1f}% ({max_month})")
        
        # グラフ表示
        col1, col2 = st.columns(2)
        
        # 月別オーダー数の棒グラフ
        with col1:
            st.subheader("月別オーダー数")
            fig_orders = px.bar(
                monthly_data, 
                x='year_month', 
                y='total_orders',
                title="月別オーダー数推移",
                labels={'year_month': '年月', 'total_orders': 'オーダー数'},
                color='total_orders',
                color_continuous_scale='Blues'
            )
            fig_orders.update_layout(
                xaxis_tickangle=-45,
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_orders, use_container_width=True)
        
        # 月別キャンセル率の線グラフ
        with col2:
            st.subheader("月別キャンセル率")
            fig_cancel = px.line(
                monthly_data, 
                x='year_month', 
                y='cancel_rate',
                title="月別キャンセル率推移",
                labels={'year_month': '年月', 'cancel_rate': 'キャンセル率(%)'},
                markers=True
            )
            fig_cancel.update_traces(
                line=dict(color='red', width=3),
                marker=dict(size=8, color='darkred')
            )
            fig_cancel.update_layout(
                xaxis_tickangle=-45,
                height=400,
                yaxis=dict(title='キャンセル率(%)', ticksuffix='%')
            )
            st.plotly_chart(fig_cancel, use_container_width=True)
        
        # 詳細データテーブル
        st.subheader("月別詳細データ")
        st.dataframe(
            monthly_data.rename(columns={
                'year_month': '年月',
                'total_orders': '総注文数',
                'cancelled_orders': 'キャンセル数',
                'cancel_rate': 'キャンセル率(%)'
            }),
            use_container_width=True
        )
    else:
        st.warning("月別分析データを準備できませんでした")
else:
    st.error("注文データが読み込めませんでした")

# 元のデータ表示セクション
st.header("📊 データ概要")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Orders Data (Top 10 rows)")
    if not orders_df.empty:
        st.dataframe(orders_df.head(10))
    else:
        st.warning("注文データがありません")

with col2:
    st.subheader("Users Data (Top 10 rows)")
    if not users_df.empty:
        st.dataframe(users_df.head(10))
    else:
        st.warning("ユーザーデータがありません")