# -*- coding: utf-8 -*-
"""Check what fund types are available in the dataset"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import akshare as ak
import pandas as pd

print("Fetching fund data...")
df = ak.fund_etf_fund_daily_em()

if df is not None and not df.empty:
    print(f"Total funds: {len(df)}")

    # Find the type column
    type_col = None
    for col in df.columns:
        if '类型' in str(col):
            type_col = col
            break

    if type_col:
        print(f"\nType column found: {repr(type_col)}")
        print(f"\nUnique fund types:")
        print(df[type_col].value_counts())

        print(f"\nSample of funds with 'LOF' in name:")
        lof_in_name = df[df[df.columns[1]].str.contains('LOF', na=False)]
        print(f"Found {len(lof_in_name)} funds with 'LOF' in name")

        if not lof_in_name.empty:
            print("\nFirst 5 examples:")
            for idx, row in lof_in_name.head(5).iterrows():
                print(f"  Code: {row[df.columns[0]]}, Name: {row[df.columns[1]]}, Type: {row[type_col]}")

        # Save all data to check
        df.to_csv("test/all_fund_data_sample.csv", index=False, encoding='utf-8-sig')
        print(f"\nFull dataset saved to: test/all_fund_data_sample.csv")

    else:
        print("ERROR: Could not find type column")
        print(f"Columns: {list(df.columns)}")

else:
    print("ERROR: No data returned")
