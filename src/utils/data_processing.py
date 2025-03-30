from typing import List, Dict, Any
import pandas as pd

def aggregate_dataframe(df: pd.DataFrame, group_by: List[str], agg_funcs: Dict[str, Any]) -> pd.DataFrame:
    """Aggregate DataFrame with multiple aggregation functions"""
    return df.groupby(group_by).agg(agg_funcs).reset_index()

def filter_dataframe(df: pd.DataFrame, conditions: Dict[str, Any]) -> pd.DataFrame:
    """Filter DataFrame based on multiple conditions"""
    mask = pd.Series(True, index=df.index)
    for column, value in conditions.items():
        if isinstance(value, (list, tuple)):
            mask &= df[column].between(value[0], value[1])
        else:
            mask &= df[column] == value
    return df[mask]

def sort_dataframe(df: pd.DataFrame, by: List[str], ascending: List[bool] = None) -> pd.DataFrame:
    """Sort DataFrame by multiple columns"""
    if ascending is None:
        ascending = [True] * len(by)
    return df.sort_values(by=by, ascending=ascending)

def merge_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, on: str, how: str = 'inner') -> pd.DataFrame:
    """Merge two DataFrames with specified join type"""
    return pd.merge(df1, df2, on=on, how=how)

def pivot_dataframe(df: pd.DataFrame, index: str, columns: str, values: str) -> pd.DataFrame:
    """Pivot DataFrame to create a cross-tabulation"""
    return df.pivot(index=index, columns=columns, values=values)

def melt_dataframe(df: pd.DataFrame, id_vars: List[str], value_vars: List[str]) -> pd.DataFrame:
    """Melt DataFrame to convert wide format to long format"""
    return pd.melt(df, id_vars=id_vars, value_vars=value_vars)
