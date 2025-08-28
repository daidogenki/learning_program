#!/usr/bin/env python3
"""
Test script for chatbot_app.py core functions
"""

import pandas as pd
import duckdb
import sys
import os

# Add current directory to path to import chatbot functions
sys.path.append('.')

# Import functions from chatbot_app
from chatbot_app import (
    load_sales_data, 
    init_duckdb, 
    build_system_prompt, 
    is_safe_sql, 
    fallback_sql, 
    run_sql,
    auto_chart,
    summarize_result
)

def test_basic_functions():
    """Test core chatbot functions"""
    print("🧪 Testing chatbot functions...")
    
    # Test 1: Data loading
    print("\n1. Testing data loading...")
    try:
        # Mock streamlit functions for testing
        import streamlit as st
        st.error = print
        st.stop = lambda: None
        
        sales_df = load_sales_data()
        print(f"✅ Data loaded successfully: {len(sales_df)} rows")
        print(f"   Columns: {list(sales_df.columns)}")
        print(f"   Date range: {sales_df['date'].min()} to {sales_df['date'].max()}")
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False
    
    # Test 2: DuckDB initialization
    print("\n2. Testing DuckDB initialization...")
    try:
        con = init_duckdb(sales_df)
        
        # Test the sales view
        test_query = "SELECT COUNT(*) as total FROM sales"
        result = con.execute(test_query).fetchone()
        print(f"✅ DuckDB initialized: {result[0]} records in sales view")
        
        # Test month column
        month_query = "SELECT DISTINCT month FROM sales ORDER BY month LIMIT 3"
        months = con.execute(month_query).fetchall()
        print(f"   Sample months: {[m[0] for m in months]}")
        
    except Exception as e:
        print(f"❌ DuckDB initialization failed: {e}")
        return False
    
    # Test 3: SQL safety checks
    print("\n3. Testing SQL safety...")
    safe_queries = [
        "SELECT * FROM sales",
        "SELECT category, SUM(revenue) FROM sales GROUP BY category",
        "SELECT month, category, SUM(revenue) as total_revenue FROM sales GROUP BY month, category ORDER BY month"
    ]
    
    unsafe_queries = [
        "DROP TABLE sales",
        "INSERT INTO sales VALUES (1,2,3)",
        "SELECT * FROM sales; DROP TABLE sales",
        "UPDATE sales SET revenue = 0"
    ]
    
    for query in safe_queries:
        if not is_safe_sql(query):
            print(f"❌ Safe query marked as unsafe: {query}")
            return False
    print("✅ Safe queries passed")
    
    for query in unsafe_queries:
        if is_safe_sql(query):
            print(f"❌ Unsafe query marked as safe: {query}")
            return False
    print("✅ Unsafe queries blocked")
    
    # Test 4: Fallback SQL
    print("\n4. Testing fallback SQL...")
    test_cases = [
        ("月毎のカテゴリ別の売り上げ", "month"),
        ("チャネルごとの売上", "sales_channel"),
        ("地域別の売上", "region"),
        ("総売上", "total_revenue")
    ]
    
    for msg, expected in test_cases:
        fallback = fallback_sql(msg)
        if expected in fallback.lower():
            print(f"✅ Fallback for '{msg}': correct pattern")
        else:
            print(f"❌ Fallback for '{msg}': unexpected result")
    
    # Test 5: SQL execution
    print("\n5. Testing SQL execution...")
    try:
        # Test representative queries
        queries = [
            "SELECT month, category, SUM(revenue) AS total_revenue FROM sales GROUP BY month, category ORDER BY month, category",
            "SELECT sales_channel, SUM(revenue) AS total_revenue FROM sales GROUP BY sales_channel ORDER BY total_revenue DESC",
            "SELECT region, SUM(revenue) AS total_revenue FROM sales GROUP BY region ORDER BY total_revenue DESC"
        ]
        
        for i, query in enumerate(queries, 1):
            result_df = run_sql(con, query)
            print(f"✅ Query {i} executed: {len(result_df)} rows, columns: {list(result_df.columns)}")
            
            # Test summarization
            summary = summarize_result(result_df)
            print(f"   Summary: {summary}")
            
            if i == 1:  # Show sample data for first query
                print(f"   Sample data:\n{result_df.head(3).to_string()}")
                
    except Exception as e:
        print(f"❌ SQL execution failed: {e}")
        return False
    
    # Test 6: System prompt
    print("\n6. Testing system prompt...")
    prompt = build_system_prompt()
    required_elements = [
        "既存の sales テーブル",
        "SELECT 文を1本だけ", 
        "DDL/DML/複数文/セミコロン",
        "month 列",
        "SUM(revenue)"
    ]
    
    for element in required_elements:
        if element not in prompt:
            print(f"❌ System prompt missing: {element}")
            return False
    print("✅ System prompt contains required elements")
    
    print("\n🎉 All tests passed successfully!")
    return True

if __name__ == "__main__":
    success = test_basic_functions()
    if not success:
        sys.exit(1)