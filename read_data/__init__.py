from typing import List, Optional

import pandas as pd

from utils.constants import INTERVALS


def add_period_cols(df: pd.DataFrame, cols: Optional[List[str]] = None) -> None:
    """
    Adds columns for the month, quarter, and year in which the date value lies.

    Parameters:
        df (pd.DataFrame): DataFrame to add the columns to.
        cols (Optional[List[str]]): Column names to create new columns based on. 
            If not provided, uses all columns whose names include 'Date'.
        
    Example:
        >>> df = pd.DataFrame({'Created Date': ['2023-01-15', '2023-04-20']})
        >>> df['Created Date'] = pd.to_datetime(df['Created Date'])
        >>> add_period_cols(df)
        >>> print(df)
            Created Date  Created Month Created Quarter Created Year
        0     2023-01-15        2023-01         2023Q1        2023
        1     2023-04-20        2023-04         2023Q2        2023
    """
    if cols is None:
        cols = [col for col in df.columns if 'Date' in col]
    for interval_ in INTERVALS:
        for col in cols:
            df[col.replace('Date', interval_)] = df[col].dt.to_period(interval_[0])


def correct_date_dtype(
    df: pd.DataFrame, 
    date_columns: Optional[List[str]] = None, 
    date_format: str = '%Y-%m-%d'
) -> pd.DataFrame:
    """
    Convert the specified columns of a DataFrame to datetime type.

    Parameters:
        df (pd.DataFrame): DataFrame whose column types to convert.
        date_columns (Optional[List[str]]): Columns whose types to convert. Defaults to None. 
            If None, converts all columns whose names contain "Date".
        date_format (str): The format to use when parsing dates. Defaults to '%Y-%m-%d'.

    Returns:
        pd.DataFrame: The modified DataFrame with specified columns converted to datetime.
    """
    if date_columns is None:
        date_columns = [col for col in df.columns if 'Date' in col]

    df[date_columns] = (
        df[date_columns]
        .astype(str)
        .apply(lambda col: col.str.split('T').str[0])
        .apply(pd.to_datetime, errors='coerce', format=date_format)
    )
    df[date_columns] = df[date_columns].apply(lambda col: col.dt.tz_localize(None))
    return df
          