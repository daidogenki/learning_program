import streamlit as st
from openai import OpenAI
import pandas as pd

# OpenAIのクライアントを初期化します
client = OpenAI()

# アプリのタイトルを設定します
st.title('販売データ分析AIチャットボット')

# --- ここからデータ読み込みと事前準備 ---
try:
    df = pd.read_csv('data/sample_sales.csv')

    # AIがデータを理解しやすいように、データの内容をテキスト形式に変換します
    data_description = f"""
    あなたは、与えられた販売データに関する質問に答えるAIチャットボットです。
    ユーザーからの質問に対し、必要に応じて**提供されたPythonコードの計算結果**を基に回答を生成してください。
    このデータはカンマ区切りのCSV形式で、以下の列を含みます。

    - date: 販売日 (YYYY-MM-DD形式)
    - category: 商品カテゴリ (例: Electronics, Groceries, Apparel, Books, Home & Kitchen, Sports, Beauty)
    - units: 販売数量
    - unit_price: 単価
    - region: 販売地域 (例: North, East, South, West)
    - sales_channel: 販売経路 (例: Online, Store)
    - customer_segment: 顧客セグメント (例: Small Business, Consumer)
    - revenue: 売上金額 (units * unit_price で計算されます)

    データの最初の5行は以下の通りです:
    {df.head().to_csv(index=False)}

    全データの統計情報（describe()の結果）は以下の通りです:
    {df.describe().to_csv()}

    データに関する質問には、この情報に基づいて答えてください。
    """
    # ここに、よくある質問に対する事前計算結果を格納する辞書を用意します
    category_revenue_df = df.groupby('category')['revenue'].sum().reset_index()
    category_revenue_info = category_revenue_df.to_string(index=False) # AIに渡すための整形

    # 新しく追加された列に関する集計も例として追加
    region_revenue_df = df.groupby('region')['revenue'].sum().reset_index()
    region_revenue_info = region_revenue_df.to_string(index=False)

    sales_channel_revenue_df = df.groupby('sales_channel')['revenue'].sum().reset_index()
    sales_channel_revenue_info = sales_channel_revenue_df.to_string(index=False)

except FileNotFoundError:
    st.error('data/sample_sales.csv が見つかりません。ファイルパスを確認してください。')
    st.stop()
except Exception as e:
    st.error(f'データの読み込み中にエラーが発生しました: {e}')
    st.stop()
# --- ここまでデータ読み込みと事前準備 ---


# チャット履歴を保存するための場所を用意します
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 初回起動時にAIにデータの内容と役割を伝えるシステムメッセージ
    st.session_state.messages.append({"role": "system", "content": data_description})
    st.session_state.messages.append({"role": "assistant", "content": "こんにちは！販売データに関するご質問に何でもお答えします。例：'カテゴリごとの売上は？'、'一番売上が高い商品は？'、'オンライン販売の売上は？'など。"}) # ヒントを更新


# これまでのチャット履歴を表示します
for message in st.session_state.messages:
    if message["role"] != "system": # システムメッセージは表示しない
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ユーザーからの新しいメッセージを受け取る入力欄を表示します
if prompt := st.chat_input("データに関する質問をしてください..."):
    # ユーザーのメッセージを履歴に追加して表示します
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- ここからAIへのプロンプト構築ロジックの変更 ---
    messages_for_ai = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages if m["role"] != "system"
    ]

    final_messages_to_send = [
        {"role": "system", "content": data_description}
    ] + messages_for_ai

    # ユーザーの質問に応じて、追加のコンテキストをAIに提供します
    # 例: 「カテゴリごとの売上は？」という質問に対応
    if "カテゴリ" in prompt and ("売上" in prompt or "売り上げ" in prompt):
        final_messages_to_send.append({
            "role": "user",
            "content": f"以下のデータは、カテゴリごとの合計売上です。この情報を使って、ユーザーの質問に答えてください。\n\n{category_revenue_info}\n\n質問：{prompt}"
        })
    # 新しく追加された列に関する質問への対応例
    elif "地域" in prompt and ("売上" in prompt or "売り上げ" in prompt):
        final_messages_to_send.append({
            "role": "user",
            "content": f"以下のデータは、地域ごとの合計売上です。この情報を使って、ユーザーの質問に答えてください。\n\n{region_revenue_info}\n\n質問：{prompt}"
        })
    elif "販売経路" in prompt or "オンライン" in prompt or "店舗" in prompt or "チャネル" in prompt:
         final_messages_to_send.append({
            "role": "user",
            "content": f"以下のデータは、販売経路ごとの合計売上です。この情報を使って、ユーザーの質問に答えてください。\n\n{sales_channel_revenue_info}\n\n質問：{prompt}"
        })
    # --- ここまでAIへのプロンプト構築ロジックの変更 ---

    # AIに応答を生成してもらう部分です
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=final_messages_to_send,
            stream=True,
        )
        response = st.write_stream(stream)
    # AIの応答を履歴に追加します
    st.session_state.messages.append({"role": "assistant", "content": response})