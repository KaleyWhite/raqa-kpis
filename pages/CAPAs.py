import os
from typing import Optional, Tuple, Union

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import streamlit as st

from read_data.read_capas import read_capa_data
from utils import compute_bin_width, compute_cts, init_page, show_data_srcs
from utils.constants import ALL_PERIODS, DATE_COLS
from utils.filters import render_breakdown_fixed, render_interval_filter, render_period_filter, render_toggle
from utils.plotting import display_no_data_msg, plot_bar, responsive_columns
from utils.text_fmt import period_str


if __name__ == '__main__':
    init_page('CAPAs')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]


def ct_by_submission_date(
    interval: Optional[str] = 'Month',
    filter_by_selection: bool = True
) -> Optional[pd.Series]:
    """
    Counts the number of CAPAs submitted during each period in the user-selected time interval.
    Missing periods are filled with zero.

    Parameters
    ----------
    interval (Optional[str]): Time interval to group by ('Month', 'Quarter', 'Year'). 
        Defaults to 'Month'.
    filter_by_selection (bool): If True, only consider CAPAs of the user-selected filters. 
        Defaults to True.

    Returns
    -------
    Optional[pd.Series]
        Series indexed by period, containing the number of CAPAs submitted in each period.
        Returns None if `df_capas` is not available (e.g., is a placeholder string).
    """
    if isinstance(df_capas, str):
        return

    df_capas_ = filtered_df_capas.copy() if filter_by_selection else df_capas.copy()
    df_capas_ = df_capas_[df_capas_['Status'] == 'Closed']

    period_col = interval + ' of Submission'
    by_submission_date = (
        df_capas_.groupby(period_col)
        .size()
        .reindex(ALL_PERIODS[interval], fill_value=0)
    )

    return by_submission_date


def compute_avg_time_open(
    interval: Optional[str] = 'Month',
    filter_by_selection: bool = True
) -> Optional[pd.Series]:
    """
    Computes the average number of days CAPAs were open per period.

    Parameters
    ----------
    interval : Optional[str]
        Time interval to compute the average days open ('Month', 'Quarter', 'Year').
        Defaults to 'Month'.
    filter_by_selection : bool
        If True, only consider CAPAs of the user-selected filters. Defaults to True.

    Returns
    -------
    Optional[pd.Series]
        Series indexed by period, containing the average days CAPAs were open.
        Returns None if `df_capas` is unavailable (e.g., is a placeholder string).
    """
    if isinstance(df_capas, str):
        return None

    # Select appropriate dataframe
    df_capas_ = filtered_df_capas.copy() if filter_by_selection else df_capas.copy()
    df_capas_ = df_capas_[df_capas_['Status'] == 'Closed']

    period_col = interval + ' of Submission'

    # Compute average Age per period
    avg_age = df_capas_.groupby(period_col)['Age'].mean().reindex(ALL_PERIODS[interval])

    return avg_age


def compute_capa_commitment(
    interval: Optional[str] = 'Month',
    filter_by_selection: bool = True
) -> Optional[pd.Series]:
    """
    Returns CAPA commitment (percent of CAPAs submitted on or before their due date) 
    for each period in which a CAPA for one of the user-selected problem types was submitted.

    Parameters
    ----------
    interval (Optional[str]): Time interval to group by ('Month', 'Quarter', 'Year'). 
        Defaults to 'Month'.
    filter_by_selection (bool): If True, only consider CAPAs of the user-selected filters. 
        Defaults to True.

    Returns
    -------
    Optional[pd.Series]
        Series indexed by period, containing CAPA commitment percentages.
        Returns None if `df_capas` is not available (e.g., is a placeholder string).
    """
    if isinstance(df_capas, str):
        return

    submitted = ct_by_submission_date(interval, filter_by_selection)
    if submitted is None or submitted.empty:
        return

    df_capas_ = filtered_df_capas.copy() if filter_by_selection else df_capas.copy()
    df_capas_ = df_capas_[df_capas_['Status'] == 'Closed']
    
    period_col = interval + ' of Submission'
    ct_on_time = (
        df_capas_[df_capas_['Date of Submission'] <= df_capas_['Due Date']]
        .groupby(period_col)
        .size()
        .reindex(ALL_PERIODS[interval], fill_value=0)
    )

    commitment = ct_on_time / submitted * 100

    return commitment


def compute_capa_effectiveness(
    interval: Optional[str] = 'Month', 
    filter_by_selection: bool = True
) -> Optional[pd.Series]:
    """
    Computes CAPA effectiveness over time.

    CAPA effectiveness is defined as the percentage of CAPAs that passed the 
    effectiveness verification check for each period in which a CAPA for one 
    of the user-selected problem types was submitted.

    Parameters
    ----------
    interval (Optional[str]): Time interval to compute effectiveness ('Month', 'Quarter', 'Year').
        Defaults to 'Month'.
    filter_by_selection (bool): If True, only consider CAPAs of the user-selected filters. 
        Defaults to True.

    Returns
    -------
    Optional[pd.Series]
        Series indexed by period, containing CAPA effectiveness percentages.
        Returns None if `df_capas` is not available (e.g., is a string placeholder).
    """
    if isinstance(df_capas, str):
        return

    # Get the count of CAPAs submitted per period
    submitted = ct_by_submission_date(interval, filter_by_selection)

    # Select appropriate dataframe
    df_capas_ = filtered_df_capas.copy() if filter_by_selection else df_capas.copy()
    df_capas_ = df_capas_[df_capas_['Status'] == 'Closed']

    # Count CAPAs that passed effectiveness verification per period
    passed_col = 'Effectiveness Verification Status'
    period_col = interval + ' of Submission'
    ct_passed = (
        df_capas_[df_capas_[passed_col] == 'Pass']
        .groupby(period_col)
        .size()
        .reindex(ALL_PERIODS[interval], fill_value=0)
    )

    # Compute effectiveness percentage
    effectiveness = ct_passed / submitted * 100

    return effectiveness


def compute_submitted_timely(
    interval: Optional[str] = 'Month', 
    filter_by_selection: bool = True
) -> Optional[pd.Series]:
    """
    Computes the percentage of CAPAs submitted within 90 days of being opened.

    Parameters
    ----------
    interval (Optional[str]): Time interval to compute percentage submitted timely ('Month', 'Quarter', 'Year').
        Defaults to 'Month'.
    filter_by_selection (bool): If True, only consider CAPAs of the user-selected filters. 
        Defaults to True.

    Returns
    -------
    Optional[pd.Series]
        Series indexed by period, containing percentage CAPAs submitted timely.
        Returns None if `df_capas` is not available (e.g., is a string placeholder).
    """
    if isinstance(df_capas, str):
        return

    # Get the count of CAPAs submitted per period
    submitted = ct_by_submission_date(interval, filter_by_selection)

    # Select appropriate dataframe
    df_capas_ = filtered_df_capas.copy() if filter_by_selection else df_capas.copy()
    df_capas_ = df_capas_[df_capas_['Status'] == 'Closed']

    # Count CAPAs submitted within 90 days of creation date
    period_col = interval + ' of Submission'
    ct_timely = (
        df_capas_[df_capas_['Age'] <= 90]
        .groupby(period_col)
        .size()
        .reindex(ALL_PERIODS[interval], fill_value=0)
    )

    # Compute timely percentage
    pct_timely = ct_timely / submitted * 100

    return pct_timely


def plot_capa_age() -> Union[Tuple[plt.Figure, plt.Axes], str]:
    """
    Plots a histogram of open CAPAs by age, highlighting CAPAs older than 1 year.

    The function separates open CAPAs into:
      - CAPAs < 365 days (green bars)
      - CAPAs >= 365 days (red bars)
    
    It includes:
      - A vertical dotted gray line at 365 days labeled "1y"
      - A red transparent shaded region from 365 days to the end of the plot
      - A red label at the top-right showing the percentage of CAPAs older than 1 year
      
    If there are no open CAPAs, returns empty axes with a "no data" message

    Returns:
        Tuple[plt.Figure, plt.Axes]:
            Matplotlib Figure and Axes objects
    """
    fig, ax = plt.subplots()
    ax.set_title('CAPA Age')
    
    if 'data' in st.session_state and not st.session_state['data']:
        display_no_data_msg('Toggle "Data" on in the sidebar to plot!', fig, ax)
        return fig, ax
    
    open_capas = filtered_df_capas[filtered_df_capas['Status'] == 'Open']
    if len(open_capas) == 0:
        display_no_data_msg('No open CAPAs, so cannot plot CAPA age.', fig, ax)
        return fig, ax
    
    open_short = open_capas[open_capas['Age'] < 365]
    open_long = open_capas[open_capas['Age'] >= 365]
    
    # Compute bin width
    bin_width = compute_bin_width([open_capas['Age']]) / 5
    overall_min, overall_max = open_capas['Age'].min(), open_capas['Age'].max()
    bins = np.arange(overall_min, overall_max + bin_width, bin_width)
    
    # Plot histograms
    open_short['Age'].plot(kind='hist', ax=ax, color='green', bins=bins, edgecolor='black')
    open_long['Age'].plot(kind='hist', ax=ax, color='red', bins=bins, edgecolor='black')
    
    # Vertical line at 365 days
    ax.axvline(365, color='gray', linestyle='dotted', linewidth=1)
    ax.text(365 + 5, ax.get_ylim()[1] * 0.05, '1y', color='black', ha='center', va='top', fontsize=12, fontweight='bold')
    
    # Red shaded region for CAPAs >= 365 days
    x_max = ax.get_xlim()[1]
    ax.axvspan(365, x_max, facecolor='red', alpha=0.1, edgecolor='gray')
    
    # Percent annotation at top-right
    pct_long = len(open_long) / len(open_capas) * 100
    ax.text(
        x_max * 0.95, ax.get_ylim()[1] * 0.95,         
        f"{pct_long:.1f}% open >1y",
        color='red',
        ha='right', va='top', fontsize=12, fontweight='bold'
    )
    
    # Titles and labels
    ax.set_xlabel('# Days Open')
    ax.set_ylabel('# Open CAPAs')
    
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    
    return fig, ax


df_capas = read_capa_data()

     
if __name__ == '__main__':  
    st.title('CAPAs')
    show_data_srcs('CAPAs', df_capas if isinstance(df_capas, str) else None)
    if not isinstance(df_capas, str):       
        to_display = []
        
        render_toggle(release_dates=False)
        interval = render_interval_filter(PAGE_NAME)
        min_period = df_capas[list(DATE_COLS['CAPAs'])].min().min().to_period(interval[0])
        start, end = render_period_filter(PAGE_NAME, min_period)
        
        filtered_df_capas = render_breakdown_fixed('CAPAs', df_capas)
    
        min_period_msg = ' as earlier CAPAs than this ' + interval.lower() + ' are not tracked in Matrix'
        period_string = 'during ' + period_str(start, interval) if start == end else 'between ' + period_str(start, interval) + ' and ' + period_str(end, interval)
        for col, short in DATE_COLS['CAPAs'].items():
            df_to_ct = (filtered_df_capas[filtered_df_capas['Status'] == 'Closed'] if short in ['Submitted', 'Approved'] else filtered_df_capas).copy() 
            capa_cts = compute_cts('CAPAs', df_to_ct)
            total_cts, cts_by_selection = capa_cts[col]
            plot = plot_bar(
                PAGE_NAME,
                total_cts, 
                grouped_data=cts_by_selection, 
                min_period=min_period,
                min_period_msg=min_period_msg,
                max_period_msg=' as there may be more CAPAs ' + short.lower() + ' this ' + interval.lower(), 
                clip_min=0,
                title='# CAPAs ' + short,
                y_label='# CAPAs',
                y_integer=True,
                missing_as_zero=True,
                no_data_msg=f'No CAPAs meeting the selected criteria were {short.lower()} {period_string}, so cannot plot CAPAs {short.lower()}.'
            )
            to_display.append(plot[0])
        commitment_effectiveness_max_period_msg = ' as there may be more CAPAs submitted this ' + interval.lower()
        plot = plot_bar(
            PAGE_NAME,
            compute_capa_commitment(interval),
            min_period=min_period,
            min_period_msg=min_period_msg,
            max_period_msg=commitment_effectiveness_max_period_msg,
            title='% CAPAs Submitted by Due Date',
            x_label='Submission ' + interval,
            y_label='Commitment %',
            is_pct=True,
            label_missing='No CAPAs submitted',
            no_data_msg=f'No CAPAs meeting the selected criteria were submitted {period_string}, so cannot plot CAPA commitment.'
        )
        to_display.append(plot[0])
        plot = plot_bar(
            PAGE_NAME,
            compute_capa_effectiveness(interval),
            min_period=min_period,
            min_period_msg=min_period_msg,
            max_period_msg=commitment_effectiveness_max_period_msg,
            title='CAPA Effectiveness',
            x_label='Submission ' + interval,
            y_label='% passed effectiveness check',
            is_pct=True,
            label_missing='No CAPAs submitted',
            no_data_msg=f'No CAPAs meeting the selected criteria were submitted {period_string}, so cannot plot CAPA effectiveness.'
        )
        to_display.append(plot[0])
        
        plot = plot_bar(
            PAGE_NAME,
            compute_submitted_timely(interval),
            min_period=min_period,
            min_period_msg=min_period_msg,
            max_period_msg=commitment_effectiveness_max_period_msg,
            title='CAPAs Submitted Within 90d',
            x_label='Submission ' + interval,
            y_label='% Submitted W/in 90d',
            is_pct=True,
            label_missing='No CAPAs submitted',
            no_data_msg=f'No CAPAs meeting the selected criteria were submitted {period_string}, so cannot plot CAPAs submitted in a timely manner.'
        )
        to_display.append(plot[0])
        
        plot = plot_bar(
            PAGE_NAME,
            compute_avg_time_open(interval),
            min_period=min_period,
            bar_kwargs={'label': '_nolegend_'},
            min_period_msg=min_period_msg,
            max_period_msg=commitment_effectiveness_max_period_msg,
            title='Average Time to Submission',
            x_label='Submission ' + interval,
            y_label='# Days',
            clip_min=0,
            y_integer=True,
            label_missing='No CAPAs submitted',
            no_data_msg=f'No CAPAs were submitted {period_string}, so cannot plot average number of days until closure.'
        )
        to_display.append(plot[0])
            
        plot = plot_capa_age()
        to_display.append(plot[0])
        
        responsive_columns(to_display)
