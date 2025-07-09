import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
import re
from typing import Dict, List, Any, Optional

# OpenAIクライアントの初期化
client = OpenAI()

class SalesDataAnalyzer:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df['month'] = self.df['date'].dt.month
        self.df['day'] = self.df['date'].dt.day
        self.df['weekday'] = self.df['date'].dt.day_name()
        
    def get_data_summary(self) -> Dict[str, Any]:
        """データの基本統計情報を返す"""
        return {
            'total_records': len(self.df),
            'date_range': f"{self.df['date'].min().strftime('%Y-%m-%d')} to {self.df['date'].max().strftime('%Y-%m-%d')}",
            'categories': self.df['category'].unique().tolist(),
            'regions': self.df['region'].unique().tolist(),
            'channels': self.df['sales_channel'].unique().tolist(),
            'segments': self.df['customer_segment'].unique().tolist(),
            'total_revenue': self.df['revenue'].sum(),
            'total_units': self.df['units'].sum(),
            'avg_unit_price': self.df['unit_price'].mean(),
        }
    
    def get_revenue_by_category(self) -> pd.DataFrame:
        """カテゴリ別売上を取得"""
        return self.df.groupby('category')['revenue'].sum().sort_values(ascending=False)
    
    def get_revenue_by_region(self) -> pd.DataFrame:
        """地域別売上を取得"""
        return self.df.groupby('region')['revenue'].sum().sort_values(ascending=False)
    
    def get_revenue_by_channel(self) -> pd.DataFrame:
        """販売チャネル別売上を取得"""
        return self.df.groupby('sales_channel')['revenue'].sum().sort_values(ascending=False)
    
    def get_revenue_by_segment(self) -> pd.DataFrame:
        """顧客セグメント別売上を取得"""
        return self.df.groupby('customer_segment')['revenue'].sum().sort_values(ascending=False)
    
    def get_daily_revenue_trend(self) -> pd.DataFrame:
        """日別売上トレンドを取得"""
        return self.df.groupby('date')['revenue'].sum().reset_index()
    
    def get_monthly_revenue_trend(self) -> pd.DataFrame:
        """月別売上トレンドを取得"""
        return self.df.groupby('month')['revenue'].sum().reset_index()
    
    def get_top_performing_products(self, n: int = 5) -> pd.DataFrame:
        """売上上位商品を取得"""
        return self.df.groupby('category').agg({
            'revenue': 'sum',
            'units': 'sum',
            'unit_price': 'mean'
        }).sort_values('revenue', ascending=False).head(n)
    
    def get_filtered_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """条件でデータをフィルタリング"""
        filtered_df = self.df.copy()
        
        for key, value in filters.items():
            if key == 'date_range' and value:
                if len(value) == 2:
                    filtered_df = filtered_df[
                        (filtered_df['date'] >= value[0]) & 
                        (filtered_df['date'] <= value[1])
                    ]
            elif key in filtered_df.columns and value:
                if isinstance(value, list):
                    filtered_df = filtered_df[filtered_df[key].isin(value)]
                else:
                    filtered_df = filtered_df[filtered_df[key] == value]
        
        return filtered_df
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """質問を分析して適切なデータ分析を実行"""
        question_lower = question.lower()
        
        # 基本統計に関する質問
        if any(word in question_lower for word in ['総売上', 'total revenue', '全体', 'overall', 'summary', 'サマリー']):
            summary = self.get_data_summary()
            return {
                'type': 'summary',
                'data': summary,
                'answer': f"総売上: ¥{summary['total_revenue']:,}\n総販売数: {summary['total_units']:,}個\n平均単価: ¥{summary['avg_unit_price']:,.0f}\nデータ期間: {summary['date_range']}"
            }
        
        # カテゴリ別分析
        elif any(word in question_lower for word in ['category', 'カテゴリ', '商品', 'product']):
            data = self.get_revenue_by_category()
            return {
                'type': 'category_analysis',
                'data': data,
                'answer': f"カテゴリ別売上:\n" + "\n".join([f"{cat}: ¥{rev:,}" for cat, rev in data.head().items()])
            }
        
        # 地域別分析
        elif any(word in question_lower for word in ['region', '地域', 'エリア', 'area']):
            data = self.get_revenue_by_region()
            return {
                'type': 'region_analysis',
                'data': data,
                'answer': f"地域別売上:\n" + "\n".join([f"{region}: ¥{rev:,}" for region, rev in data.items()])
            }
        
        # チャネル別分析
        elif any(word in question_lower for word in ['channel', 'チャネル', 'online', 'store', 'オンライン', '店舗']):
            data = self.get_revenue_by_channel()
            return {
                'type': 'channel_analysis',
                'data': data,
                'answer': f"販売チャネル別売上:\n" + "\n".join([f"{channel}: ¥{rev:,}" for channel, rev in data.items()])
            }
        
        # セグメント別分析
        elif any(word in question_lower for word in ['segment', 'セグメント', 'customer', '顧客']):
            data = self.get_revenue_by_segment()
            return {
                'type': 'segment_analysis',
                'data': data,
                'answer': f"顧客セグメント別売上:\n" + "\n".join([f"{segment}: ¥{rev:,}" for segment, rev in data.items()])
            }
        
        # トレンド分析
        elif any(word in question_lower for word in ['trend', 'トレンド', '推移', '変化', 'change']):
            data = self.get_daily_revenue_trend()
            return {
                'type': 'trend_analysis',
                'data': data,
                'answer': f"売上推移データを取得しました。最高売上日: {data.loc[data['revenue'].idxmax(), 'date'].strftime('%Y-%m-%d')} (¥{data['revenue'].max():,})"
            }
        
        # トップ商品分析
        elif any(word in question_lower for word in ['top', 'best', 'トップ', '上位', '最高']):
            data = self.get_top_performing_products()
            return {
                'type': 'top_products',
                'data': data,
                'answer': f"売上上位商品:\n" + "\n".join([f"{idx+1}. {cat}: ¥{row['revenue']:,}" for idx, (cat, row) in enumerate(data.head().iterrows())])
            }
        
        # 一般的な質問
        else:
            summary = self.get_data_summary()
            return {
                'type': 'general',
                'data': summary,
                'answer': "データについて詳しく教えてください。カテゴリ別、地域別、チャネル別、セグメント別の分析や、トレンド分析、トップ商品分析などが可能です。"
            }

def create_chart(analysis_result: Dict[str, Any]) -> Optional[go.Figure]:
    """分析結果に基づいてチャートを作成"""
    if analysis_result['type'] == 'category_analysis':
        data = analysis_result['data']
        fig = px.bar(
            x=data.index, 
            y=data.values,
            title='カテゴリ別売上',
            labels={'x': 'カテゴリ', 'y': '売上 (¥)'}
        )
        return fig
    
    elif analysis_result['type'] == 'region_analysis':
        data = analysis_result['data']
        fig = px.pie(
            values=data.values,
            names=data.index,
            title='地域別売上分布'
        )
        return fig
    
    elif analysis_result['type'] == 'channel_analysis':
        data = analysis_result['data']
        fig = px.bar(
            x=data.index,
            y=data.values,
            title='販売チャネル別売上',
            labels={'x': '販売チャネル', 'y': '売上 (¥)'}
        )
        return fig
    
    elif analysis_result['type'] == 'segment_analysis':
        data = analysis_result['data']
        fig = px.pie(
            values=data.values,
            names=data.index,
            title='顧客セグメント別売上分布'
        )
        return fig
    
    elif analysis_result['type'] == 'trend_analysis':
        data = analysis_result['data']
        fig = px.line(
            data,
            x='date',
            y='revenue',
            title='日別売上推移',
            labels={'date': '日付', 'revenue': '売上 (¥)'}
        )
        return fig
    
    elif analysis_result['type'] == 'top_products':
        data = analysis_result['data']
        fig = px.bar(
            x=data.index,
            y=data['revenue'],
            title='売上上位商品',
            labels={'x': 'カテゴリ', 'y': '売上 (¥)'}
        )
        return fig
    
    return None

# Streamlitアプリケーションのメイン部分
def main():
    st.set_page_config(page_title="Sales Data Chatbot", layout="wide")
    st.title('売上データ分析チャットボット')
    
    # データアナライザーの初期化
    @st.cache_data
    def load_analyzer():
        return SalesDataAnalyzer('data/sample_sales.csv')
    
    try:
        analyzer = load_analyzer()
        
        # サイドバーでデータサマリー表示
        with st.sidebar:
            st.header("データサマリー")
            summary = analyzer.get_data_summary()
            st.metric("総売上", f"¥{summary['total_revenue']:,}")
            st.metric("総販売数", f"{summary['total_units']:,}個")
            st.metric("平均単価", f"¥{summary['avg_unit_price']:,.0f}")
            st.write(f"**データ期間**: {summary['date_range']}")
            st.write(f"**カテゴリ数**: {len(summary['categories'])}")
            st.write(f"**地域数**: {len(summary['regions'])}")
            
            # 使用可能な質問例
            st.header("質問例")
            st.write("- 総売上を教えて")
            st.write("- カテゴリ別の売上は？")
            st.write("- 地域別の売上分析")
            st.write("- オンラインと店舗の売上比較")
            st.write("- 売上トレンドを見せて")
            st.write("- トップ商品は？")
            st.write("- 顧客セグメント別の分析")
        
        # チャット履歴の初期化
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # チャット履歴の表示
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "chart" in message:
                    st.plotly_chart(message["chart"], use_container_width=True)
        
        # ユーザー入力の処理
        if prompt := st.chat_input("売上データについて質問してください..."):
            # ユーザーメッセージを履歴に追加
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 分析実行
            with st.chat_message("assistant"):
                with st.spinner("データを分析中..."):
                    # データ分析の実行
                    analysis_result = analyzer.analyze_question(prompt)
                    
                    # 基本的な回答の表示
                    st.markdown(analysis_result['answer'])
                    
                    # チャートの作成・表示
                    chart = create_chart(analysis_result)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                    
                    # AIによる詳細な分析と洞察
                    context = f"""
                    ユーザーの質問: {prompt}
                    
                    データ分析結果:
                    {analysis_result['answer']}
                    
                    データサマリー:
                    - 総売上: ¥{summary['total_revenue']:,}
                    - 総販売数: {summary['total_units']:,}個
                    - データ期間: {summary['date_range']}
                    - 取り扱いカテゴリ: {', '.join(summary['categories'])}
                    - 対象地域: {', '.join(summary['regions'])}
                    
                    上記のデータ分析結果をもとに、ビジネスインサイトや改善提案を含む詳細な分析レポートを日本語で提供してください。
                    数字は正確に使用し、具体的な actionable insights を提供してください。
                    """
                    
                    # OpenAI APIを使用した詳細分析
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "あなたは売上データの専門アナリストです。提供されたデータを分析し、ビジネスに役立つ洞察と具体的な改善提案を提供してください。"},
                                {"role": "user", "content": context}
                            ],
                            temperature=0.7
                        )
                        
                        ai_analysis = response.choices[0].message.content
                        st.markdown("---")
                        st.markdown("**🤖 AI分析レポート:**")
                        st.markdown(ai_analysis)
                        
                        # メッセージを履歴に追加
                        assistant_message = {
                            "role": "assistant", 
                            "content": f"{analysis_result['answer']}\n\n---\n\n**🤖 AI分析レポート:**\n{ai_analysis}"
                        }
                        if chart:
                            assistant_message["chart"] = chart
                        
                        st.session_state.messages.append(assistant_message)
                        
                    except Exception as e:
                        st.error(f"AI分析でエラーが発生しました: {str(e)}")
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": analysis_result['answer']
                        })
        
    except FileNotFoundError:
        st.error("データファイル 'data/sample_sales.csv' が見つかりません。")
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()