from datetime import datetime
import random

from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import pandas as pd


# Constants

DATE_COLS = {
    'AE': {
        'Date Received': 'Received'
    },
    'CAPA': {
        'Date Created': 'Opened', 
        'Due Date': 'Due', 
        'Date of Submission': 'Submitted', 
        'Date of Final Approval': 'Approved'
    },
    'Complaint': {
        'Complaint Created Date': 'Opened', 
        'Complaint Received Date': 'Received', 
        'Investigation Completed Date': 'Investigation Completed',
        'Completed Date': 'Closed'
    }
}
PROD_COLORS = {
    'AutoContour': '#f2b740',
    'ClearCalc': '#4286f4',
    'ClearCheck': '#184664',
    'ChartCheck': '#1f8a4c',
    'EZFluence': '#960052',
    'Limbus Contour': '#33314D',
    'QuickCode': '#27ad60',
    'RadMachine': '#12502c',
    'RadMachine-Diagnostic': '#12502c',
    'RadMonteCarlo': '#0099e1',
    'RadOrthanc': '#2a82bd',
    'N/A': '#a0a0a0'
}
RAD_COLOR = '#3498db'
RAD_DATE = '2016-10-26'
ALL_PERIODS = {
    'Month': pd.period_range(start=RAD_DATE, end=datetime.now().strftime('%Y-%m'), freq='M'),
    'Quarter': pd.period_range(start=RAD_DATE, end=datetime.now().strftime('%Y-%m'), freq='Q')
}


# Functions

def add_period_cols(df, cols=None):
    """Adds columns for the month and quarter  in which the date value lies.

    Parameters:
        df (pd.DataFrame): `DataFrame` to add the columns to
        cols (Optional[List[str]]): Column names to create new columns based on. If not provided, uses all columns whose names include "date".
        
    Example:
        >>> df = pd.DataFrame({'Created Date': ['2023-01-15', '2023-04-20']})
        >>> df['Created Date'] = pd.to_datetime(df['Created Date'])
        >>> add_period_columns(df)
        >>> print(df)
            Created Date  Created Month Created Quarter
        0     2023-01-15  2023-01       2023Q1
        1     2023-04-20  2023-04       2023Q2
    """
    if cols is None:
        cols = [col for col in df.columns if 'Date' in col]
    for interval_ in ['Month', 'Quarter']:
        for col in cols:
            df[col.replace('Date', interval_)] = df[col].dt.to_period(interval_[0])


def correct_date_dtype(df, date_columns=None):
    """Convert the given `DataFrame` columns to `pd.datetime` type.

    Parameters:
        df (pd.DataFrame): _DataFrame whose column types to convert
        date_columns (Optional[List[str]]): Columns whose types to convert. Defaults to None. If None, converts all columns whose names contain "Date".

    Returns:
        df: The modified `DataFrame`
    """
    if date_columns is None:
        date_columns = [col for col in df.columns if 'Date' in col]
    df[date_columns] = df[date_columns].apply(pd.to_datetime, errors='coerce').apply(lambda col: col.dt.tz_localize(None))
    return df


def create_shifted_cmap(cmap_name, shift=None):
    """Returns a new `ListedColormap` based on a shifted version of a named colormap.

    This function takes a named Matplotlib colormap (e.g., 'tab10') and rotates its list of colors 
    by the specified amount. If `shift` is not provided, a random shift is applied.

    Parameters:
        cmap_name (str): The name of a discrete colormap available in Matplotlib.
        shift (Optional[int]): The number of colors to rotate the colormap by. 
                               If None, a random shift between 1 and (N-1) is used, 
                               where N is the number of colors in the colormap.

    Returns:
        matplotlib.colors.ListedColormap: A new colormap with colors rotated from the original.

    Example:
        >>> shifted_cmap = create_shifted_cmap('tab10', shift=3)
        >>> plt.bar(range(10), [1]*10, color=[shifted_cmap(i) for i in range(10)])
    """
    cmap = plt.get_cmap(cmap_name)
    colors = cmap.colors
    if shift is None:
        shift = random.randint(1, len(colors) - 1)
    shifted_colors = colors[shift:] + colors[:shift]
    return ListedColormap(shifted_colors)
