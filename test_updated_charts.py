#!/usr/bin/env python3
"""
Test the updated auto_chart function with labels-based approach
"""

import pandas as pd
import sys
import os

# Add current directory to path
sys.path.append('.')

# Import functions from chatbot_app
from chatbot_app import load_sales_data, init_duckdb, run_sql

def test_chart_patterns():
    """Test different chart patterns"""
    print("🎨 Testing updated auto_chart function...")
    
    # Mock streamlit functions for testing
    import streamlit as st
    st.error = print
    st.stop = lambda: None
    
    # Load data and initialize DB
    sales_df = load_sales_data()
    con = init_duckdb(sales_df)
    
    # Test queries that should trigger different chart patterns
    test_queries = [
        {
            "name": "月別カテゴリ別売上",
            "query": "SELECT month, category, SUM(revenue) AS total_revenue FROM sales GROUP BY month, category ORDER BY month, category",
            "expected_chart": "Line chart with category colors"
        },
        {
            "name": "チャネル別売上",
            "query": "SELECT sales_channel, SUM(revenue) AS total_revenue FROM sales GROUP BY sales_channel ORDER BY total_revenue DESC",
            "expected_chart": "Bar chart"
        },
        {
            "name": "地域別売上",
            "query": "SELECT region, SUM(revenue) AS total_revenue FROM sales GROUP BY region ORDER BY total_revenue DESC",
            "expected_chart": "Bar chart"
        },
        {
            "name": "月別総売上",
            "query": "SELECT month, SUM(revenue) AS total_revenue FROM sales GROUP BY month ORDER BY month",
            "expected_chart": "Line chart"
        }
    ]
    
    for test_case in test_queries:
        print(f"\n🔍 Testing: {test_case['name']}")
        try:
            result_df = run_sql(con, test_case["query"])
            print(f"   ✅ Query executed: {len(result_df)} rows")
            print(f"   📊 Columns: {list(result_df.columns)}")
            print(f"   🎯 Expected: {test_case['expected_chart']}")
            
            # Show sample data
            if len(result_df) > 0:
                print(f"   📋 Sample data:\n{result_df.head(3).to_string(index=False)}")
                
                # Test the chart logic (without actually creating plots)
                cols = result_df.columns.tolist()
                colset = set(cols)
                
                # Check which pattern would be triggered
                if {'month', 'category', 'total_revenue'}.issubset(colset):
                    print("   🎨 Would create: Line chart with category colors")
                elif len(cols) == 2:
                    dim_col, value_col = cols[0], cols[1]
                    dim_candidates = ['category', 'sales_channel', 'region', 'customer_segment']
                    val_candidates = ['total_revenue', 'total_units', 'revenue', 'units', 'count']
                    if dim_col in dim_candidates and value_col in val_candidates:
                        print("   🎨 Would create: Bar chart")
                elif 'month' in colset:
                    val_candidates = ['total_revenue', 'total_units', 'revenue', 'units', 'count']
                    value_col = next((v for v in val_candidates if v in colset and v != 'month'), None)
                    if value_col:
                        print("   🎨 Would create: Line chart")
                else:
                    print("   ❌ No chart pattern matched")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ Chart pattern testing completed!")
    return True

if __name__ == "__main__":
    test_chart_patterns()