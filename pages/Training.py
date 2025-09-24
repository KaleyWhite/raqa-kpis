from datetime import datetime
import os
from typing import Dict, List, Optional, Tuple

from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import streamlit as st

from read_data.read_training import read_training_data
from utils import init_page, show_data_srcs, suppress_warnings
from utils.constants import ALL_PERIODS, INTERVALS, PROD_COLORS, RAD_COLOR
from utils.filters import render_interval_filter, render_period_filter
from utils.plotting import plot_bar, responsive_columns
from utils.text_fmt import period_str


if __name__ == '__main__':
    init_page('QMS Training')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]
suppress_warnings()


@st.cache_data
def get_training_by_qtr_yr(df_training_mo: pd.DataFrame) -> List[pd.DataFrame]:
    """
    Aggregates monthly training data into quarterly and yearly summaries per user.

    Groups the input DataFrame by consecutive rows with the same user and quarter/year,
    summing numeric columns for each group. A `GroupID` is used to preserve continuity
    when multiple records exist for the same user in the same period.

    Parameters
    ----------
    df_training_mo (pd.DataFrame): DataFrame containing monthly training records,
        with at least 'Quarter', 'Year', and 'User' columns.

    Returns
    -------
    List[pd.DataFrame]:
        List of DataFrames with one row per user per quarter/year, containing
        the summed numeric training metrics.
        Index 0 corresponds to quarterly aggregation, index 1 to yearly aggregation.
    """
    by_period = []
    for interval_ in ['Quarter', 'Year']:
        df_training_by_period = df_training_mo.copy()
        group = (
            (df_training_by_period[interval_] != df_training_by_period[interval_].shift())
            | (df_training_by_period['User'] != df_training_by_period['User'].shift())
        )
        df_training_by_period['GroupID'] = group.cumsum()
        numeric_cols = [col for col in df_training_by_period.columns if col not in INTERVALS]
        df_training_by_period = (
            df_training_by_period.groupby(['GroupID', interval_, 'User'], as_index=False)[numeric_cols]
            .sum()
            .drop(columns='GroupID')
        )
        by_period.append(df_training_by_period)

    return by_period


@st.cache_data
def compute_training_commitment(
    min_period: Optional[pd.Period] = None,
    max_period: Optional[pd.Period] = None
) -> Optional[Dict[str, pd.Series]]:
    """
    Computes the percentage of trainings completed on time for each interval (Month, Quarter, Year).

    For each interval:
    - Aggregates the number of trainings completed and completed on time.
    - Calculates the percentage of trainings completed on time.
    - Reindexes the result to cover the full range from `min_period` to `max_period`, filling missing values with 0.

    Parameters
    ----------
    min_period (Optional[pd.Period]): Minimum date (month, quarter, or year) to compute training commitment for.
        If not provided, uses Rad incorporation date.
    max_period (Optional[pd.Period]): Maximum date (month, quarter, or year) to compute training commitment for.
        If not provided, uses today's date.

    Returns
    -------
    Optional[Dict[str, pd.Series]]:
        Dictionary with interval names (values from INTERVALS) as keys and corresponding pandas Series
        of "% Trainings Completed on Time" as values, indexed by period.
        Returns None if training data was not retrieved.
    """
    if isinstance(dfs_training, str):
        return None

    commitment = {}
    for interval_ in INTERVALS:
        periods = (
            ALL_PERIODS[interval_]
            if min_period is None
            else pd.period_range(start=min_period, end=max_period, freq=interval_[0])
        )

        df_training_grouped = dfs_training[interval_].groupby(
            interval_, as_index=False
        )[
            [col for col in dfs_training[interval_].columns if col not in INTERVALS]
        ].sum()

        df_training_grouped['% Trainings Completed on Time'] = (
            df_training_grouped['# Trainings Completed on Time']
            / df_training_grouped['# Trainings Completed'].replace(0, np.nan)
            * 100
        )

        df_training_grouped = (
            pd.DataFrame({interval_: periods})
            .merge(df_training_grouped, on=interval_, how='left')
            .set_index(interval_)
            .fillna(0)
        )

        commitment[interval_] = df_training_grouped['% Trainings Completed on Time']

    return commitment
    
    
def plot_training_completion() -> Optional[Tuple[Figure, Axes]]:
    """
    Plots a histogram of employees' training completion percentages for the current period.

    Checks whether any training records exist for the current period within the user-selected
    `interval` (value from INTERVALS). If records are present, generates a histogram showing
    the distribution of '% Training Complete' across employees.

    The plot includes:
    - x-axis: Percent of training completed (0–100%)
    - y-axis: Number of employees
    - Title with the current date

    Returns
    -------
    Optional[Tuple[Figure, Axes]]:
        fig (Figure): Matplotlib Figure object.
        ax (Axes): Matplotlib Axes object.
        Returns None if no training records are available for the current period.
    """
    curr_period_training = dfs_training[interval][
        dfs_training[interval][interval] == ALL_PERIODS[interval][-1]
    ]
    if len(curr_period_training) == 0:
        st.write(
            'No training was assigned for this ' +
            interval.lower() +
            ', so cannot plot training completion.'
        )
        return None

    fig, ax = plt.subplots()
    ax.grid(axis='y', alpha=0.7, zorder=1)

    cts, _, _ = ax.hist(
        curr_period_training['% Training Complete'],
        color=RAD_COLOR,
        edgecolor='black',
        zorder=2
    )

    ax.set_xlim(0, 100)
    ax.set_ylim(0, max(cts))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_xlabel('% Complete')
    ax.set_ylabel('# Employees')
    ax.set_title('Training Completion as of ' + datetime.now().strftime('%Y-%m-%d'))

    return fig, ax
     
     
df_training_mo = read_training_data()
dfs_training = None
if isinstance(df_training_mo, pd.DataFrame):
    by_qtr, by_yr = get_training_by_qtr_yr(df_training_mo)
    dfs_training = {'Month': df_training_mo, 'Quarter': by_qtr, 'Year': by_yr}


if __name__ == '__main__':
    st.title('QMS Training')
    st.markdown('**Note**: This is dummy data! REAL QMS training stats will be provided once we roll out QMS training in Matrix!')
    show_data_srcs('Training', df_training_mo if isinstance(df_training_mo, str) else None)
    if not isinstance(df_training_mo, str):
        interval = render_interval_filter(PAGE_NAME)
        training_commitment_percentage = compute_training_commitment()
        min_period = df_training_mo[interval].min()
        start, end = render_period_filter(PAGE_NAME, interval, min_period)

        to_display = []
        period_string = 'during ' + period_str(start, interval) if start == end else 'between ' + period_str(start, interval) + ' and ' + period_str(end, interval)
        plot = plot_bar(
            PAGE_NAME,
            compute_training_commitment()[interval],
            interval=interval,
            start=start,
            end=end,
            bar_kwargs={'color': PROD_COLORS['N/A'], 'label': '_nolegend_'},
            tol_lower=80,
            min_period=min_period, 
            min_period_msg=f' as Rad did not implement the current QMS training process until partway through the {interval.lower()}', 
            is_pct=True,
            title='Training Commitment',
            y_label='% Trainings completed on time'
        )
        to_display.append(f'No training matching the selected crietria was completed {period_string}.' if plot is None else plot[0])
        plot = plot_training_completion()
        if plot is not None:
            to_display.append(plot[0])
        
        responsive_columns(to_display)
        