import re
from typing import Dict, List, Optional

import pandas as pd


def series_to_float(series: pd.Series) -> pd.Series:
    """
    将Series转换为float类型，处理百分号、逗号等

    Args:
        series: 输入的Series

    Returns:
        转换后的Series
    """
    cleaned = (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    cleaned = cleaned.replace({"-": "", "--": "", "nan": "", "None": ""})
    return pd.to_numeric(cleaned, errors="coerce")


def find_column(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
    """
    根据关键词列表查找列名

    Args:
        df: DataFrame
        keywords: 关键词列表

    Returns:
        找到的列名，如果没找到返回None
    """
    for col in df.columns:
        col_text = str(col)
        for keyword in keywords:
            if keyword in col_text:
                return col
    return None


def find_code_column_index(df: pd.DataFrame) -> int:
    """
    查找代码列的索引（6位数字）

    Args:
        df: DataFrame

    Returns:
        代码列的索引
    """
    if df is None or df.empty:
        return 0

    best_idx = 0
    best_score = -1.0
    sample = min(50, len(df))
    pattern = re.compile(r"^\d{6}$")

    for idx in range(df.shape[1]):
        values = df.iloc[:sample, idx].astype(str)
        if values.empty:
            continue
        hits = values.str.match(pattern).sum()
        score = hits / len(values)
        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx


def prepare_lof_df(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    准备LOF DataFrame，添加标准化的代码列

    Args:
        df: 输入的DataFrame

    Returns:
        处理后的DataFrame
    """
    if df is None or df.empty:
        return None

    df = df.copy()
    code_idx = find_code_column_index(df)
    df["_code"] = df.iloc[:, code_idx].astype(str).str.zfill(6)
    return df


def order_by_codes(df: pd.DataFrame, codes: List[str]) -> pd.DataFrame:
    """
    按照指定的代码顺序排序DataFrame

    Args:
        df: DataFrame
        codes: 代码列表

    Returns:
        排序后的DataFrame
    """
    if not codes or df.empty:
        return df

    order = {code: idx for idx, code in enumerate(codes)}
    df = df.copy()
    df["_order"] = df["_code"].map(order)
    return df.sort_values("_order").drop(columns="_order")


def get_column_map(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    获取常用列的映射

    Args:
        df: DataFrame

    Returns:
        列名映射字典
    """
    return {
        "name": find_column(df, ["名称", "简称"]),
        "price": find_column(df, ["最新价", "最新", "现价"]),
        "pct": find_column(df, ["涨跌幅"]),
        "limit_up": find_column(df, ["涨停价", "涨停"]),
        "limit_down": find_column(df, ["跌停价", "跌停"]),
        "prev_close": find_column(df, ["昨收", "前收", "昨收盘"]),
    }


def compute_pct_series(
    df: pd.DataFrame, cols: Dict[str, Optional[str]]
) -> Optional[pd.Series]:
    """
    计算涨跌幅Series

    Args:
        df: DataFrame
        cols: 列名映射

    Returns:
        涨跌幅Series
    """
    if cols["pct"]:
        return series_to_float(df[cols["pct"]])

    if cols["price"] and cols["prev_close"]:
        price = series_to_float(df[cols["price"]])
        prev = series_to_float(df[cols["prev_close"]])
        safe_prev = prev.where(prev != 0)
        return (price - safe_prev) / safe_prev * 100.0

    return None


def fmt_value(value, digits: int = 2) -> str:
    """
    格式化数值

    Args:
        value: 数值
        digits: 小数位数

    Returns:
        格式化后的字符串
    """
    if value is None:
        return "-"
    try:
        if pd.isna(value):
            return "-"
    except Exception:
        pass
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)
