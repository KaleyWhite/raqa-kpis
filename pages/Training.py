from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import streamlit as st

from utils import PROD_COLORS, RAD_COLOR
from utils.filters import render_interval_filter, render_period_filter
from utils.plotting import plot_bar
from utils.read_data import read_training
from utils.text_fmt import period_str


@st.cache_data
def get_training_by_qtr(df_training_mo):
    """
    Aggregates monthly training data into quarterly summaries per user.

    Groups the input DataFrame by consecutive rows with the same user and quarter,
    and sums numeric columns for each group. A `GroupID` is used to preserve
    continuity in grouping when multiple records exist for the same user in the same quarter.

    Parameters:
        df_training_mo (pd.DataFrame): DataFrame containing monthly training records
            with at least 'Quarter' and 'User' columns.

    Returns:
        pd.DataFrame: A `DataFrame` with one row per user per quarter, containing
            the summed numeric training metrics.
    """
    df_training_by_qtr = df_training_mo.copy()
    group = (df_training_by_qtr['Quarter'] != df_training_by_qtr['Quarter'].shift()) | (df_training_by_qtr['User'] != df_training_by_qtr['User'].shift())
    df_training_by_qtr['GroupID'] = group.cumsum()
    df_training_by_qtr = df_training_by_qtr.groupby(['GroupID', 'Quarter', 'User'], as_index=False).sum(numeric_only=True).drop(columns='GroupID')  
    
    return df_training_by_qtr


@st.cache_data
def compute_training_commitment():
    """
    Computes the percentage of trainings completed on time for each interval (Month and Quarter).

    For each interval:
    - Aggregates the number of trainings completed and completed on time.
    - Calculates the percentage of trainings completed on time.
    - Reindexes the result to cover the full range from `min_period` to `max_period`, filling missing values with 0.

    Returns:
        dict: A dictionary with interval names ('Month', 'Quarter') as keys and corresponding
              pandas Series of "% Trainings Completed on Time" as values, indexed by period.
    """
    commitment = {}
    for interval_ in ['Month', 'Quarter']:
        df_training_grouped = dfs_training[interval_].groupby(interval_, as_index=False)[[col for col in dfs_training[interval_].columns if col not in ['Month', 'Quarter']]].sum()
        df_training_grouped['% Trainings Completed on Time'] = df_training_grouped['# Trainings Completed on Time'] / df_training_grouped['# Trainings Completed'].replace(0, np.nan) * 100
        df_training_grouped = pd.DataFrame({interval: pd.period_range(start=min_period, end=max_period, freq=interval[0])}).merge(df_training_grouped, on=interval_, how='left').set_index(interval_).fillna(0)
        commitment[interval_] = df_training_grouped['% Trainings Completed on Time']
    return commitment
    
    
def plot_training_completion():
    """
    Plots a histogram of employees' training completion percentages for the current period.

    The function checks whether any training records exist for the current period (`max_period`)
    within the user-selected `interval` ('Month' or 'Quarter'). If records are present, it generates
    a histogram showing the distribution of `% Training Complete` across employees.

    The plot includes:
    - X-axis: Percent of training completed (0–100%)
    - Y-axis: Number of employees
    - Title with the current date

    If no training was assigned for the current interval, a message is displayed instead.

    Returns:
        None
    """
    curr_period_training = dfs_training[interval][dfs_training[interval][interval] == max_period]
    if len(curr_period_training) == 0:
        st.write('No training was assigned for this ' + interval.lower() + '.')
        return
    fig, ax = plt.subplots()
    ax.grid(axis='y', alpha=0.7, zorder=1)
    cts, _, _ = ax.hist(curr_period_training['% Training Complete'], color=RAD_COLOR, edgecolor='black', zorder=2)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, max(cts))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_xlabel('% Complete')
    ax.set_ylabel('# Employees')
    ax.set_title('Training Completion as of ' + datetime.now().strftime('%Y-%m-%d'))
    
    st.pyplot(fig)
     
     
df_training_mo = read_training()
dfs_training = {'Month': df_training_mo, 'Quarter': get_training_by_qtr(df_training_mo)}


if __name__ == '__main__':
    st.title('QMS Training')
    st.markdown('**Note**: This is dummy data! REAL QMS training stats will be provided once we roll out QMS training in Matrix!')

    interval = render_interval_filter()
    training_commitment_percentage = compute_training_commitment()
    min_period = df_training_mo[interval].min()
    max_period = pd.to_datetime('today').to_period(interval[0])
    render_period_filter(min_period)
    start = st.session_state.get('start_period')
    end = st.session_state.get('end_period')

    plot = plot_bar(
        compute_training_commitment()[interval],
        interval=interval,
        start=start,
        end=end, 
        no_data_msg='No training was completed ' + ('during ' + period_str(start, interval) if start == end else 'between ' + period_str(start, interval) + ' and ' + period_str(end, interval)) + '.',
        bar_kwargs={'color': PROD_COLORS['N/A'], 'label': '_nolegend_'},
        tol_lower=80,
        min_period=min_period, 
        min_period_msg=' as Rad did not implement the current QMS training process until partway through the ' + interval.lower(), 
        is_pct=True,
        title='Training Commitment',
        y_label='% Trainings completed on time'
    )
    if plot is not None:
        st.pyplot(plot[0])

    plot_training_completion()
