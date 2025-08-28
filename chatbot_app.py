"""
売上データ分析AIチャットボット (DuckDB + NL→SQL)

Setup Commands:
uv add streamlit duckdb pandas plotly openai>=1.30.0
# For Anthropic API (optional):
# uv add anthropic

Run Command:
uv run streamlit run chatbot_app.py

Environment Variables:
OPENAI_API_KEY (required)
# or ANTHROPIC_API_KEY (if using Anthropic)
"""

import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import re
import os
from typing import Optional, Tuple
import io

# LLM Client Setup
try:
    import openai
    LLM_PROVIDER = "openai"
except ImportError:
    try:
        import anthropic
        LLM_PROVIDER = "anthropic"
    except ImportError:
        st.error("Please install either openai or anthropic: uv add openai>=1.30.0")
        st.stop()

# Required columns for validation
REQUIRED_COLUMNS = ['date', 'category', 'units', 'unit_price', 'region', 'sales_channel', 'customer_segment', 'revenue']

# Blocked SQL keywords for safety
BLOCKED_KEYWORDS = ['insert', 'update', 'delete', 'drop', 'alter', 'create', 'replace', 'attach', 'copy', 'pragma', 'script', 'call', ';']

def load_sales_data() -> pd.DataFrame:
    """Load and validate existing CSV data with required transformations"""
    csv_path = "data/sample_sales.csv"
    
    # Check if file exists
    if not os.path.exists(csv_path):
        st.error(f"❌ Required file not found: {csv_path}")
        st.error("Please ensure the CSV file exists before running the application.")
        st.stop()
    
    try:
        # Load CSV
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            st.error(f"❌ Missing required columns: {missing_cols}")
            st.error(f"Required columns: {REQUIRED_COLUMNS}")
            st.stop()
        
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Fill missing revenue with units * unit_price (in-memory only)
        if df['revenue'].isnull().any():
            df['revenue'] = df['revenue'].fillna(df['units'] * df['unit_price'])
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading CSV file: {str(e)}")
        st.stop()

def init_duckdb(df: pd.DataFrame) -> duckdb.DuckDBPyConnection:
    """Initialize DuckDB with sales view"""
    con = duckdb.connect(':memory:')
    
    # Register DataFrame
    con.register('sales_df', df)
    
    # Create sales view with month column
    con.execute("""
        CREATE OR REPLACE VIEW sales AS
        SELECT
            date,
            date_trunc('month', date)::date AS month,
            category,
            units,
            unit_price,
            region,
            sales_channel,
            customer_segment,
            revenue
        FROM sales_df
    """)
    
    return con

def build_system_prompt(max_rows: int = 5000) -> str:
    """Build system prompt for LLM with strict constraints"""
    return f"""あなたは既存の sales テーブルのみを対象とする DuckDB用SQLアシスタント。

重要な制約:
- 新規データの生成・仮定は禁止。既存CSVの内容だけを前提とする
- SELECT 文を1本だけ出力。DDL/DML/複数文/セミコロンは禁止
- 月次は month 列を使用。不明瞭な「売上」は SUM(revenue) と解釈
- 必要に応じ LIMIT {max_rows} を付与

スキーマ (sales テーブル):
- date: 日付
- month: 月初日 (date_trunc('month', date)::date)
- category: カテゴリ
- units: 数量
- unit_price: 単価  
- region: 地域
- sales_channel: 販売チャネル
- customer_segment: 顧客セグメント
- revenue: 売上金額

例:
SELECT month, category, SUM(revenue) AS total_revenue
FROM sales
GROUP BY month, category
ORDER BY month, category

SELECT sales_channel, SUM(revenue) AS total_revenue
FROM sales
GROUP BY sales_channel
ORDER BY total_revenue DESC

SELECT region, SUM(revenue) AS total_revenue
FROM sales
GROUP BY region
ORDER BY total_revenue DESC

コードブロックなしで純粋なSQLのみを出力してください。"""

def generate_sql(user_msg: str) -> str:
    """Generate SQL using LLM API"""
    system_prompt = build_system_prompt()
    
    try:
        if LLM_PROVIDER == "openai":
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.1,
                max_tokens=500
            )
            sql = response.choices[0].message.content.strip()
        
        # Uncomment below for Anthropic API
        # elif LLM_PROVIDER == "anthropic":
        #     client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        #     response = client.messages.create(
        #         model="claude-3-haiku-20240307",
        #         max_tokens=500,
        #         temperature=0.1,
        #         messages=[
        #             {"role": "user", "content": f"{system_prompt}\n\n{user_msg}"}
        #         ]
        #     )
        #     sql = response.content[0].text.strip()
        
        else:
            raise ValueError("No supported LLM provider available")
        
        # Remove code block markers if present
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        sql = sql.strip()
        
        return sql
        
    except Exception as e:
        st.error(f"LLM API Error: {str(e)}")
        return fallback_sql(user_msg)

def is_safe_sql(sql: str) -> bool:
    """Check if SQL is safe to execute"""
    sql_lower = sql.lower().strip()
    
    # Check for blocked keywords
    for keyword in BLOCKED_KEYWORDS:
        if keyword in sql_lower:
            return False
    
    # Must start with SELECT
    if not sql_lower.startswith('select'):
        return False
    
    # Must be single statement (no semicolons)
    if ';' in sql:
        return False
    
    return True

def fallback_sql(user_msg: str) -> str:
    """Return fallback SQL based on user message patterns"""
    msg_lower = user_msg.lower()
    
    if any(word in msg_lower for word in ['月', 'カテゴリ', 'category', 'month']):
        return """SELECT month, category, SUM(revenue) AS total_revenue
FROM sales
GROUP BY month, category
ORDER BY month, category"""
    
    elif any(word in msg_lower for word in ['チャネル', 'channel']):
        return """SELECT sales_channel, SUM(revenue) AS total_revenue
FROM sales
GROUP BY sales_channel
ORDER BY total_revenue DESC"""
    
    elif any(word in msg_lower for word in ['地域', 'region']):
        return """SELECT region, SUM(revenue) AS total_revenue
FROM sales
GROUP BY region
ORDER BY total_revenue DESC"""
    
    else:
        return """SELECT SUM(revenue) AS total_revenue FROM sales"""

def run_sql(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    """Execute SQL and return DataFrame"""
    # Add LIMIT if not present
    if 'limit' not in sql.lower():
        sql = sql.rstrip(';') + ' LIMIT 5000'
    
    try:
        result = con.execute(sql).df()
        return result
    except Exception as e:
        raise Exception(f"SQL実行エラー: {str(e)}")

def auto_chart(df: pd.DataFrame) -> None:
    """Generate automatic chart based on DataFrame structure (Plotly Express, labels-based)"""
    if df.empty:
        return

    cols = df.columns.tolist()
    colset = set(cols)

    # 候補列
    dim_candidates = ['category', 'sales_channel', 'region', 'customer_segment']
    val_candidates = ['total_revenue', 'total_units', 'revenue', 'units', 'count']

    # 1) month, category, total_revenue -> 折れ線（色=category）
    if {'month', 'category', 'total_revenue'}.issubset(colset):
        fig = px.line(
            df.sort_values('month'),
            x='month', y='total_revenue', color='category',
            title='月別・カテゴリ別 売上推移',
            labels={'month': '月', 'total_revenue': '売上', 'category': 'カテゴリ'}
        )
        st.plotly_chart(fig, use_container_width=True)
        return

    # 2) 次元×値 -> 棒
    if len(cols) == 2:
        dim_col, value_col = cols[0], cols[1]
        if dim_col in dim_candidates and value_col in val_candidates:
            fig = px.bar(
                df,
                x=dim_col, y=value_col,
                title=f'{dim_col} 別 {value_col}',
                labels={dim_col: dim_col, value_col: value_col}
            )
            st.plotly_chart(fig, use_container_width=True)
            return

    # 3) month×値 -> 折れ線
    if 'month' in colset:
        value_col = next((v for v in val_candidates if v in colset and v != 'month'), None)
        if value_col:
            fig = px.line(
                df.sort_values('month'),
                x='month', y=value_col,
                title=f'月別 {value_col} 推移',
                labels={'month': '月', value_col: value_col}
            )
            st.plotly_chart(fig, use_container_width=True)
            return

def summarize_result(df: pd.DataFrame) -> str:
    """Generate brief Japanese summary of results"""
    if df.empty:
        return "結果が見つかりませんでした。"
    
    # Use first 50 rows for summary
    summary_df = df.head(50)
    rows = len(summary_df)
    total_rows = len(df)
    
    summary = f"結果: {total_rows}件のデータ"
    
    # Add basic stats if numeric columns exist
    numeric_cols = summary_df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        main_col = numeric_cols[0]
        total = summary_df[main_col].sum()
        avg = summary_df[main_col].mean()
        
        if 'revenue' in main_col.lower():
            summary += f"、総売上: {total:,.0f}円、平均: {avg:,.0f}円"
        elif 'units' in main_col.lower():
            summary += f"、総数量: {total:,.0f}個、平均: {avg:,.1f}個"
    
    if total_rows > rows:
        summary += f" (上位{rows}件を表示)"
    
    return summary

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="売上データ分析AIチャットボット",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 売上データ分析AIチャットボット (DuckDB + NL→SQL)")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Load data and initialize DB
    with st.spinner("データを読み込んでいます..."):
        sales_df = load_sales_data()
        con = init_duckdb(sales_df)
    
    # Sidebar - Data Overview
    with st.sidebar:
        st.header("📈 データ概要")
        st.write(f"**総行数**: {len(sales_df):,}件")
        st.write(f"**期間**: {sales_df['date'].min().date()} ～ {sales_df['date'].max().date()}")
        st.write(f"**カテゴリ数**: {sales_df['category'].nunique()}種類")
        st.write(f"**地域数**: {sales_df['region'].nunique()}地域")
        st.write(f"**チャネル数**: {sales_df['sales_channel'].nunique()}チャネル")
        
        st.subheader("💾 元データ確認")
        csv_exists = os.path.exists("data/sample_sales.csv")
        st.write(f"CSV存在: {'✅' if csv_exists else '❌'}")
        
        # Sample data preview
        if st.button("サンプルデータ表示"):
            st.dataframe(sales_df.head())
    
    # Chat Interface
    st.subheader("💬 チャット")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "sql" in message:
                st.code(message["sql"], language="sql")
            if "dataframe" in message:
                st.dataframe(message["dataframe"])
                auto_chart(message["dataframe"])
                if "summary" in message:
                    st.info(message["summary"])
                
                # Download button
                csv_buffer = io.StringIO()
                message["dataframe"].to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 結果をCSVでダウンロード",
                    data=csv_buffer.getvalue(),
                    file_name="query_result.csv",
                    mime="text/csv"
                )
    
    # Chat input
    if prompt := st.chat_input("質問を入力してください（例：月毎のカテゴリー別の売り上げを見せて）"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and execute SQL
        with st.chat_message("assistant"):
            with st.status("分析中...", expanded=True) as status:
                st.write("🔍 SQLを生成中...")
                
                # Generate SQL
                generated_sql = generate_sql(prompt)
                
                st.write("🔒 セーフティチェック中...")
                
                # Safety check
                if not is_safe_sql(generated_sql):
                    st.write("⚠️ セーフティチェック失敗、フォールバックSQLを使用")
                    generated_sql = fallback_sql(prompt)
                
                st.write("📊 クエリ実行中...")
                
                try:
                    # Execute SQL
                    result_df = run_sql(con, generated_sql)
                    
                    if result_df.empty:
                        st.warning("結果が見つかりませんでした。")
                        response_msg = {"role": "assistant", "content": "結果が見つかりませんでした。別の質問を試してみてください。"}
                    else:
                        st.write("✨ 結果を生成中...")
                        summary = summarize_result(result_df)
                        
                        status.update(label="分析完了!", state="complete", expanded=False)
                        
                        # Display results
                        st.write("**生成されたSQL:**")
                        st.code(generated_sql, language="sql")
                        
                        st.write("**実行結果:**")
                        st.dataframe(result_df)
                        
                        # Auto chart
                        auto_chart(result_df)
                        
                        # Summary
                        st.info(f"📊 {summary}")
                        
                        # Download button
                        csv_buffer = io.StringIO()
                        result_df.to_csv(csv_buffer, index=False)
                        st.download_button(
                            label="📥 結果をCSVでダウンロード",
                            data=csv_buffer.getvalue(),
                            file_name="query_result.csv",
                            mime="text/csv"
                        )
                        
                        response_msg = {
                            "role": "assistant", 
                            "content": "分析が完了しました。",
                            "sql": generated_sql,
                            "dataframe": result_df,
                            "summary": summary
                        }
                
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
                    st.write("フォールバックSQLで再試行中...")
                    
                    try:
                        fallback_query = fallback_sql(prompt)
                        result_df = run_sql(con, fallback_query)
                        
                        if not result_df.empty:
                            summary = summarize_result(result_df)
                            st.code(fallback_query, language="sql")
                            st.dataframe(result_df)
                            auto_chart(result_df)
                            st.info(f"📊 {summary}")
                            
                            response_msg = {
                                "role": "assistant", 
                                "content": "フォールバッククエリで結果を表示しています。",
                                "sql": fallback_query,
                                "dataframe": result_df,
                                "summary": summary
                            }
                        else:
                            response_msg = {"role": "assistant", "content": "申し訳ありません。結果を取得できませんでした。"}
                    except Exception as fallback_error:
                        st.error(f"フォールバックも失敗しました: {str(fallback_error)}")
                        response_msg = {"role": "assistant", "content": "申し訳ありません。システムエラーが発生しました。"}
        
        # Add assistant response to chat history
        st.session_state.messages.append(response_msg)

if __name__ == "__main__":
    main()