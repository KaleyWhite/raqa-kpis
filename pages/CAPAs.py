import os
from typing import Optional

import pandas as pd
import streamlit as st

from read_data.read_capas import read_capa_data
from utils import compute_cts, init_page, show_data_srcs
from utils.constants import ALL_PERIODS, DATE_COLS
from utils.filters import render_breakdown_fixed, render_interval_filter, render_period_filter
from utils.plotting import plot_bar, responsive_columns
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
        return None

    df_capas_ = filtered_df_capas.copy() if filter_by_selection else df_capas.copy()

    period_col = interval + ' of Submission'
    by_submission_date = (
        df_capas_.groupby(period_col)
        .size()
        .reindex(ALL_PERIODS[interval], fill_value=0)
    )

    return by_submission_date


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
        return None

    submitted = ct_by_submission_date(interval, filter_by_selection)
    if submitted is None or submitted.empty:
        return None

    df_capas_ = filtered_df_capas.copy() if filter_by_selection else df_capas.copy()
    
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
        return None

    # Get the count of CAPAs submitted per period
    submitted = ct_by_submission_date(interval, filter_by_selection)

    # Select appropriate dataframe
    df_capas_ = filtered_df_capas.copy() if filter_by_selection else df_capas.copy()

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


df_capas = read_capa_data()
    
     
if __name__ == '__main__':  
    st.title('CAPAs')
    show_data_srcs('CAPAs', df_capas if isinstance(df_capas, str) else None)
    if not isinstance(df_capas, str):       
        to_display = []
        
        interval = render_interval_filter(PAGE_NAME)
        min_period = df_capas[list(DATE_COLS['CAPAs'])].min().min().to_period(interval[0])
        start, end = render_period_filter(PAGE_NAME, interval, min_period)
        
        filtered_df_capas = render_breakdown_fixed('CAPAs', df_capas)
        
        capa_cts = compute_cts('CAPAs', filtered_df_capas)
        min_period_msg = ' as earlier CAPAs than this ' + interval.lower() + ' are not tracked in Matrix'
        period_string = 'during ' + period_str(start, interval) if start == end else 'between ' + period_str(start, interval) + ' and ' + period_str(end, interval)
        for col, short in DATE_COLS['CAPAs'].items():
            total_cts, cts_by_selection = capa_cts[col]
            plot = plot_bar(
                PAGE_NAME,
                total_cts, 
                grouped_data=cts_by_selection, 
                bar_kwargs={'stacked': True, 'colormap': 'tab10'},
                min_period=min_period,
                min_period_msg=min_period_msg,
                max_period_msg=' as there may be more CAPAs ' + short.lower() + ' this ' + interval.lower(), 
                clip_min=0,
                title='# CAPAs ' + short,
                y_label='# CAPAs',
                y_integer=True,
                missing_as_zero=True
            )
            to_display.append(f'No CAPAs meeting the selected criteria were{short.lower()} {period_string}.' if plot is None else plot[0])
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
        )
        if plot is not None:
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
        )
        if plot is not None:
            to_display.append(plot[0])
        responsive_columns(to_display)
