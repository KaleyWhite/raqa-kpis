import os

import streamlit as st

from utils import ALL_PERIODS, DATE_COLS, INTERVALS, init_page, show_data_srcs
from utils.filters import render_interval_filter, render_period_filter
from utils.matrix import map_dropdown_ids
from utils.plotting import plot_bar, responsive_columns
from utils.read_data import read_capas
from utils.text_fmt import items_in_a_series, period_str


if __name__ == '__main__':
    init_page('CAPAs')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]


def compute_capa_cts():
    """
    Computes CAPA counts by month, quarter, and year for each CAPA-related date field,
    returning total counts and counts grouped by Problem Type.

    For each interval (value in `INTERVALS`) and CAPA date column in `DATE_COLS['CAPA']`:
        - Groups data by time period and counts total CAPAs.
        - Groups by both period and "Problem Type" to count categorized CAPAs.

    Returns:
        dict[str, dict[str, tuple[pd.Series, pd.DataFrame]]]: Nested dictionary:
            {
                'Month': {
                    'Date Created': (total_cts, cts_by_problem_type),
                    ...
                },
                'Quarter': {
                    'Date Created': (total_cts, cts_by_problem_type),
                    ...
                },
                'Year': {
                    'Date Created': (total_cts, cts_by_problem_type),
                    ...
                }
            }

    Example:
        >>> capa_cts = compute_capa_counts()
        >>> capa_cts['Month']['Date Created'][0]  # Total CAPAs opened each month
        2024-01    2
        2024-02    5
        2024-03    3
        Freq: M, dtype: int64

        >>> capa_cts['Month']['Date Created'][1]  # CAPAs opened by problem type
                  Audit Issue Customer Complaint
        2024-01       1       1
        2024-02       4       1
        2024-03       3       0
    """
    capa_cts = {}
    for interval_ in INTERVALS:
        capa_cts[interval_] = {}
        for col in DATE_COLS['CAPA']:
            period_col = col.replace('Date', interval)  # E.g., "Date Created" -> "Month Created"
            total_cts = filtered_df_capas_prob_types.groupby(period_col).size().reindex(ALL_PERIODS[interval], fill_value=0)  # Overall # CAPAs opened/due/submitted/approved during the user-selected time interval
            cts_by_prob_type = filtered_df_capas_prob_types.groupby([period_col, 'Problem Type']).size().unstack().reindex(ALL_PERIODS[interval], fill_value=0)  # # CAPAs opened/due/submitted/approved during the user-selected time interval, by type
            capa_cts[interval_][col] = (total_cts, cts_by_prob_type)
    return capa_cts


def ct_by_submission_date(interval='Month', filter_by_prob_type=True):
    """
    Counts the number of CAPAs submitted during each period in the user-selected time interval.
    Missing periods are filled with zero.
    
    Parameters:
        interval (Optional[str]): Value from `INTERVALS`. Defaults to 'Month'.
        filter_by_prob_type (Optiona[bool]): If `True`, only consider the CAPAs of the user-selected Problem Types. Defaults to `True`.

    Returns:
        Optional[pd.Series]: A `Series` indexed by period, containing the number of CAPAs submitted in each.
        Returns `None` if CAPA data was not retrieved.
    """
    if isinstance(df_capas, str):
        return
    df_capas_ = filtered_df_capas_prob_types.copy() if filter_by_prob_type else df_capas.copy()
    by_submission_date = df_capas_.groupby(interval + ' of Submission').size().reindex(ALL_PERIODS[interval], fill_value=0)  # # CAPAs submitted during each period in the interval
    
    return by_submission_date


def compute_capa_commitment(interval='Month', filter_by_prob_type=True):
    """
    Returns CAPA commitment (percent of CAPAs submitted on or before their due date) for each period in which a CAPA for one of the user-selected problem types was submitted

    Parameters:
        interval (Optional[str]): Value from `INTERVALS`. Defaults to 'Month'.
        filter_by_prob_type (Optiona[bool]): If `True`, only consider the CAPAs of the user-selected Problem Types. Defaults to `True`.
    
    Returns:
        Optional[pd.Series]: CAPA commitment for each period, indexed by period.
                             Returns `None` if CAPA data was not retrieved.
    """
    if isinstance(df_capas, str):
        return
    
    submitted = ct_by_submission_date(interval, filter_by_prob_type)
    
    df_capas_ = filtered_df_capas_prob_types.copy() if filter_by_prob_type else df_capas.copy()
    ct_on_time = df_capas_[df_capas_['Due Date'] <= df_capas_['Date of Submission']].groupby(interval + ' of Submission').size().reindex(ALL_PERIODS[interval], fill_value=0)  # # CAPAs submitted on time during each period in the interval
    
    commitment = ct_on_time / submitted * 100
    
    return commitment


def compute_capa_effectiveness(interval='Month', filter_by_prob_type=True):
    """
    Returns CAPA effectiveness (percent of CAPAs that passed effectiveness check) for each period in which a CAPA for one of the user-selected problem types was submitted

    Parameters:
        interval (Optional[str]): Value from `INTERVALS`. Defaults to 'Month'.
        filter_by_prob_type (Optiona[bool]): If `True`, only consider the CAPAs of the user-selected Problem Types. Defaults to `True`.
    
    Returns:
        Optional[pd.Series]: CAPA effectiveness for each period, indexed by period
                             Returns `None` if CAPA data was not retrieved.
    """
    if isinstance(df_capas, str):
        return
    
    submitted = ct_by_submission_date(interval, filter_by_prob_type)
    
    df_capas_ = filtered_df_capas_prob_types.copy() if filter_by_prob_type else df_capas.copy()
    ct_passed = df_capas_[df_capas_['Effectiveness Verification Status'] == 'Pass'].groupby(interval + ' of Submission').size().reindex(ALL_PERIODS[interval], fill_value=0)
    
    effectiveness = ct_passed / submitted * 100
    
    return effectiveness


df_capas = read_capas()
    
     
if __name__ == '__main__':  
    st.title('CAPAs')
    show_data_srcs('CAPAs', df_capas if isinstance(df_capas, str) else None)
    if not isinstance(df_capas, str):       
        all_prob_types = sorted(map_dropdown_ids('dd_CAPA_Problem_Types').values())
        prob_types = st.multiselect('Select Problem Types', options=all_prob_types, default=all_prob_types, key='prob_types')
        if not prob_types:
            st.write('Select problem type(s) to plot data')
        else:
            plots = []
            
            filtered_df_capas_prob_types = df_capas[df_capas['Problem Type'].isin(prob_types)]
            interval = render_interval_filter(PAGE_NAME)
            min_period = df_capas[list(DATE_COLS['CAPA'])].min().min().to_period(interval[0])
            start, end = render_period_filter(PAGE_NAME, interval, min_period)
            
            capa_cts = compute_capa_cts()[interval]
            min_period_msg = ' as earlier CAPAs than this ' + interval.lower() + ' are not tracked in Matrix'
            for col, short in DATE_COLS['CAPA'].items():
                total_cts, cts_by_prob_type = capa_cts[col]
                plot = plot_bar(
                    PAGE_NAME,
                    total_cts, 
                    grouped_data=cts_by_prob_type, 
                    bar_kwargs={'stacked': True, 'colormap': 'tab10'},
                    no_data_msg='No ' + items_in_a_series(prob_types, 'or') + ' CAPAs were ' + short.lower() + (' during ' + period_str(start, interval) if start == end else ' between ' + period_str(start, interval) + ' and ' + period_str(end, interval)) + '.',
                    min_period=min_period,
                    min_period_msg=min_period_msg,
                    max_period_msg=' as there may be more CAPAs ' + DATE_COLS['CAPA'][col].lower() + ' this ' + interval.lower(), 
                    clip_min=0,
                    title='# CAPAs ' + DATE_COLS['CAPA'][col],
                    y_label='# CAPAs',
                    y_integer=True
                )
                if plot is not None:
                    plots.append(plot[0])
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
                plots.append(plot[0])
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
                plots.append(plot[0])
            responsive_columns(plots)
