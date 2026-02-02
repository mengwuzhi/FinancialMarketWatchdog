# -*- coding: utf-8 -*-
"""Test to detect premium/discount columns with different approaches"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

print("Reading existing CSV file...")
df = pd.read_csv("test/lof_data_sample.csv", encoding='utf-8-sig')

print(f"\nTotal columns: {len(df.columns)}")
print("\nColumn analysis:")
print("-" * 80)

for i, col in enumerate(df.columns):
    print(f"Column {i}:")
    print(f"  Name (repr): {repr(col)}")
    print(f"  Name (str): {str(col)}")
    print(f"  Name (bytes): {col.encode('utf-8')}")
    print(f"  Sample values: {df[col].head(3).tolist()}")
    print()

# Check if column contains NAV or discount/premium info
print("\nSearching for potential premium/discount indicators:")
print("-" * 80)
keywords = ['折', '溢', '价', '净', 'discount', 'premium', 'nav', 'net']
for col in df.columns:
    col_lower = str(col).lower()
    for keyword in keywords:
        if keyword in str(col) or keyword in col_lower:
            print(f"Found '{keyword}' in column: {repr(col)}")
            print(f"  Sample values: {df[col].head(5).tolist()}")
            break

# Calculate potential premium if we can find NAV
print("\nColumn summary:")
print("-" * 80)
print(df.dtypes)

print("\nFirst row data:")
print("-" * 80)
print(df.iloc[0])
