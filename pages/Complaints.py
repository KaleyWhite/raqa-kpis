import os
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st

from read_data.read_complaints import read_complaint_data
from read_data.read_usage import read_usage_data
from utils import compute_cts, init_page, show_data_srcs
from utils.constants import ALL_PERIODS, DATE_COLS
from utils.filters import render_breakdown_fixed, render_interval_filter, render_period_filter, render_toggle
from utils.plotting import display_no_data_msg, plot_bar, responsive_columns
from utils.text_fmt import period_str


if __name__ == '__main__':
    init_page('Complaints')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]


def compute_complaint_pct_ratio() -> Tuple[Optional[pd.Series], Optional[pd.Series], Optional[pd.Period], Optional[List[str]]]:
    """
    Computes complaint percentage and complaint-to-user ratio for each period.

    Calculates:
    - Complaint percentage relative to device usage (complaints per 100 runs).
    - Complaint ratio (complaints per unique account).

    Aligns complaint and usage data by period and restricts calculations to periods with non-zero usage.
    Adjusts the start period if usage tracking had not yet begun, and returns explanatory messages.

    Returns
    -------
    Tuple[Optional[pd.Series], Optional[pd.Series], Optional[pd.Period], Optional[List[str]]]:
        complaint_pct (pd.Series): Percentage of complaints per usage (complaints / runs * 100).
        complaint_ratio (pd.Series): Number of complaints per unique user (account).
        pct_ratio_start (pd.Period): The period from which complaint percentage/ratio is valid.
        msgs (List[str]): Informational messages about skipped periods due to lack of usage data.
        Returns four-tuple of None's if there is no usage data during the user-selected time interval.
    """
    msgs: List[str] = []
    usage_col = 'Usage ' + interval

    if 'Complaints_Device_filter' in st.session_state:
        data_usage_device = data_usage[data_usage['Device'].isin(st.session_state['Complaints_Device_filter'])]
    else:  # Device is not filtered
        data_usage_device = data_usage

    min_usage_period = data_usage_device[usage_col].min()
    pct_ratio_start = start
    if pct_ratio_start <= min_usage_period:
        msgs.append(
            'Complaint percentage is not calculated for ' + interval.lower() + 
            's before ' + period_str(min_usage_period + 1, interval) +
            ' as Rad did not begin tracking usage for the selected devices until ' +
            period_str(min_usage_period, interval) + '.'
        )
        pct_ratio_start = min_usage_period + 1

    usage_by_period = data_usage_device.groupby(usage_col)['Number Of Runs'].sum().reindex(
        ALL_PERIODS[interval], fill_value=0
    )
    usage_by_period_filtered = usage_by_period[pct_ratio_start:end]

    total_cts, _ = compute_cts('Complaints', filtered_df_complaints)['Complaint Created Date']

    # Check for non-zero usage
    nonzero_idx = usage_by_period_filtered[usage_by_period_filtered > 0].index
    if len(nonzero_idx) == 0:
        return None, None, None, None

    complaint_pct = total_cts / usage_by_period * 100

    accts_by_period = data_usage_device.groupby(usage_col)['Account'].nunique().reindex(
        ALL_PERIODS[interval], fill_value=0
    )
    complaint_ratio = total_cts / accts_by_period

    if pct_ratio_start != start:
        msgs.append(
            'Complaint ratio is not calculated for ' + interval.lower() +
            's before ' + period_str(min_usage_period + 1, interval) +
            ' as Rad did not begin tracking usage for the selected devices until ' +
            period_str(min_usage_period, interval) + '.'
        )

    return complaint_pct, complaint_ratio, pct_ratio_start, msgs


def compute_complaint_commitment(
    interval: Optional[str] = 'Month',
    filter_by_device: bool = True
) -> Optional[pd.Series]:
    """
    Computes complaint commitment, defined as the percentage of complaints 
    that were open for 60 days or fewer, for complaints of the user-selected device,
    for each period since the first complaint for that device.

    Parameters
    ----------
    interval (Optional[str]): Time interval to group by ('Month', 'Quarter', 'Year'). Defaults to 'Month'.
    filter_by_device (bool): If True, only consider complaints for the user-selected device. Defaults to True.

    Returns
    -------
    Optional[pd.Series]: Series indexed by period, containing complaint commitment percentages.
                         Returns None if `df_complaints` is not available.
    """
    if isinstance(df_complaints, str):
        return None

    df_complaints_ = filtered_df_complaints.copy() if filter_by_device else df_complaints.copy()

    period_col = 'Completed ' + interval
    cts_by_period = df_complaints_.groupby(period_col).size().reindex(ALL_PERIODS[interval], fill_value=0)
    cts_le60_by_period = df_complaints_[df_complaints_['# Days Open'] <= 60].groupby(period_col).size().reindex(ALL_PERIODS[interval], fill_value=0)

    commitment = cts_le60_by_period / cts_by_period.replace(0, np.nan) * 100

    return commitment


df_complaints = read_complaint_data()


if __name__ == '__main__':    
    st.title('Complaints')
    data_usage = read_usage_data()
    data_src_msg = None
    if isinstance(df_complaints, str):
        if isinstance(data_usage, str):
            data_src_msg = 'Could not retrieve complaint or usage data from Salesforce.'
        else:
            data_src_msg = 'Could not retrieve complaint data from Salesforce.'
    elif isinstance(data_usage, str):
        data_src_msg = 'Could not retrieve usage data from Salesforce.'
    show_data_srcs('Complaints', data_src_msg)
    
    if not isinstance(df_complaints, str):
        to_display = []
        
        render_toggle()
        interval = render_interval_filter(PAGE_NAME)
        min_period = df_complaints[list(DATE_COLS['Complaints'])].min().min().to_period(interval[0])
        start, end = render_period_filter(PAGE_NAME, min_period)

        filtered_df_complaints = render_breakdown_fixed('Complaints', df_complaints)

        period_string = ' in ' + period_str(start, interval) if start == end else ' between ' + period_str(start, interval) + ' and ' + period_str(end, interval)
        complaint_cts = compute_cts('Complaints', filtered_df_complaints)
        for col, short in DATE_COLS['Complaints'].items():
            total_cts, cts_by_status = complaint_cts[col]
            plot = plot_bar(
                PAGE_NAME,
                total_cts,
                grouped_data=cts_by_status,
                release_dates=short in ['Opened', 'Received'],
                min_period=min_period, 
                min_period_msg=' as Rad did not implement the current complaint process until partway through the ' + interval.lower(), 
                max_period_msg=' as there may be more ' + ('complaint investigations completed' if col == 'Investigation Completed Date' else 'complaints ' + DATE_COLS['Complaints'][col].lower()) + ' this ' + interval.lower(), 
                clip_min=0,
                title='# Complaint Investigations Completed' if col == 'Investigation Completed Date' else '# Complaints ' + DATE_COLS['Complaints'][col],
                y_label='# complaints',
                y_integer=True,
                no_data_msg=f'No complaints meeting the specified criteria were {short.lower()}{period_string}.'
            )
            to_display.append(plot[0])

        complaint_pct_title, complaint_ratio_title = 'Opened Complaints as % of Usage', 'Avg # Complaints per Account'
        if isinstance(data_usage, str):
            to_display.extend([
                display_no_data_msg(f'Cannot compute complaint percentage as there is no usage data {period_str}.', title=complaint_pct_title)[0],
                display_no_data_msg(f'Cannot compute complaint ratio as there is no usage data {period_str}.', title=complaint_ratio_title)[0]
            ])
        else:
            complaint_pct, complaint_ratio, pct_ratio_start, msgs = compute_complaint_pct_ratio()
            plot = plot_bar(
                PAGE_NAME,
                complaint_pct, 
                start=pct_ratio_start.asfreq(interval[0]),
                msgs=msgs[:1],
                max_period_msg=' as there may be more complaints and usage this ' + interval.lower(), 
                clip_min=0, 
                clip_max=100,
                title=complaint_pct_title,
                y_label='% complaints'
            )
            to_display.append(plot[0])
            plot = plot_bar(
                PAGE_NAME,
                complaint_ratio, 
                start=pct_ratio_start.asfreq(interval[0]),
                msgs=msgs[1:],
                max_period_msg=' as there may be more complaints and usage this ' + interval.lower(), 
                clip_min=0, 
                clip_max=100,
                title=complaint_ratio_title,
                y_label='# complaints'
            )
            to_display.append(plot[0])

        plot = plot_bar(
            PAGE_NAME,
            compute_complaint_commitment(interval),
            max_period_msg=' as there may be more complaints closed this ' + interval.lower(), 
            is_pct=True,
            title='Complaint Commitment',
            x_label='Closure ' + interval,
            y_label='% complaints open ≤60d',
            label_missing='No complaints received',
            no_data_msg=f'No complaints were closed{period_string}, so cannot plot complaint commitment.'
        )
        to_display.append(plot[0])
        
        responsive_columns(to_display)
