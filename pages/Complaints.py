import os

import numpy as np
import streamlit as st

from utils import ALL_PERIODS, DATE_COLS, INTERVALS, PROD_COLORS, create_shifted_cmap, init_page, show_data_srcs
from utils.filters import render_interval_filter, render_period_filter
from utils.plotting import plot_bar, responsive_columns
from utils.read_data import read_complaints, read_usage
from utils.text_fmt import period_str


if __name__ == '__main__':
    init_page('Complaints')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]


def compute_complaint_cts():
    """
    Computes complaint counts by month, quarter, and year for each complaint-related date field,
    returning total counts and counts grouped by Complaint Status.

    For each interval (Value from `INTERVALS`) and complaint date column in `DATE_COLS['Complaint']`:
        - Groups data by time period and counts total complaints.
        - Groups by both period and "Complaint Status" to count categorized complaints.

    Returns:
        dict[str, dict[str, tuple[pd.Series, pd.DataFrame]]]: Nested dictionary:
            {
                'Month': {
                    'Complaint Created Date': (total_cts, cts_by_status),
                    ...
                },
                'Quarter': {
                    'Complaint Created Date': (total_cts, cts_by_status),
                    ...
                },
                'Year': {
                    'Complaint Created Date': (total_cts, cts_by_status),
                    ...
                }
            }

    Example:
        >>> complaint_cts = compute_complaint_counts()
        >>> complaint_cts['Month']['Complaint Created Date'][0]  # Total complaints created each month
        2016-10    2
        2016-11    5
        2016-12    3
        Freq: M, dtype: int64

        >>> complaint_cts['Month']['Date Created'][1]  # Complaints created by status
                   Open  Closed
        2016-10       1       1
        2016-11       4       1
        2016-12       3       0
    """
    complaint_cts = {}
    for interval_ in INTERVALS:
        complaint_cts[interval_] = {}
        for col in DATE_COLS['Complaint']:
            period_col = col.replace('Date', interval_)  # e.g., "Complaint Created Date" -> "Complaint Created Month"
            total_cts = filtered_df_complaints_device.groupby(period_col).size().reindex(ALL_PERIODS[interval_], fill_value=0)  # Overall # CAPAs opened/due/submitted/approved during the user-selected time interval
            cts_by_status = filtered_df_complaints_device.groupby([period_col, 'Complaint Status']).size().unstack().reindex(ALL_PERIODS[interval_], fill_value=0)  # # CAPAs opened/due/submitted/approved during the user-selected time interval, by type
            complaint_cts[interval_][col] = (total_cts, cts_by_status)
    return complaint_cts


def compute_complaint_pct_ratio():
    """
    Computes complaint percentage and complaint-to-user ratio for the user-selected device for each period.

    This function calculates:
    - The percentage of complaints relative to device usage (complaints per 100 runs).
    - The complaint ratio (complaints per unique account).
    
    It adjusts the start period if usage tracking had not yet begun for the selected device, and 
    returns explanatory messages accordingly. Complaint and usage data are aligned by period, 
    and calculations are restricted to periods where usage is non-zero.

    Returns:
        tuple:
            - complaint_pct (pd.Series): Percentage of complaints per usage (complaints / runs * 100).
            - complaint_ratio (pd.Series): Number of complaints per unique user (account).
            - pct_ratio_start (pd.Period): The period from which complaint percentage/ratio is valid.
            - msgs (list of str): Informational messages about skipped periods due to lack of usage data.
    """
    msgs = []
    
    data_usage = read_usage()
    data_usage_device = data_usage[data_usage['Device'] == device]
    min_usage_period = data_usage_device[interval].min()
    pct_ratio_start = start
    if pct_ratio_start <= min_usage_period:
        msgs.append('Complaint percentage is not calculated for ' + interval.lower() + 's before ' + period_str(min_usage_period + 1, interval) + ' as Rad did not begin tracking ' + device + ' usage until ' + period_str(min_usage_period, interval) + '.')
        pct_ratio_start = min_usage_period + 1
    usage_by_period = data_usage_device.groupby(interval)['Number Of Runs'].sum().reindex(ALL_PERIODS[interval], fill_value=0)
    usage_by_period_filtered = usage_by_period[pct_ratio_start:end]
    total_cts, _ = compute_complaint_cts()[interval]['Complaint Created Date']
    # Crop complaint count & usage data starting at first period w/ any usage
    nonzero_idx = usage_by_period_filtered[usage_by_period_filtered > 0].index
    if len(nonzero_idx) == 0:
        return
    complaint_pct = total_cts / usage_by_period * 100

    accts_by_period = data_usage_device.groupby(interval)['Account'].nunique().reindex(ALL_PERIODS[interval], fill_value=0)  # Salesforce accounts ("users") for each period
    complaint_ratio = total_cts / accts_by_period  # # complaints / # users
    if pct_ratio_start != start:
        msgs.append('Complaint ratio is not calculated for ' + interval.lower() + 's before ' + period_str(min_usage_period + 1, interval) + ' as Rad did not begin tracking ' + device + ' usage until ' + period_str(min_usage_period, interval) + '.') 

    return complaint_pct, complaint_ratio, pct_ratio_start, msgs


def compute_complaint_commitment(interval='Month', filter_by_device=True):
    """
    Computes complaint commitment (percentage of complaints open for 60 days or fewer) for complaints for the user-selected device, for each period since the first complaint for that device

    Parameters:
        interval (Optional[str]): Value from `INTERVALS`. Defaults to 'Month'.
        filter_by_device (Optiona[bool]): If `True`, only consider complaints about the user-selected device. Defaults to `True`.
    
    Returns:
        Optional[pd.Series]: Complaint commitment for each period, indexed by period,
        or `None` if complaint data was not retrieved
    """
    if isinstance(df_complaints, str):
        return
    df_complaints_ = filtered_df_complaints_device if filter_by_device else df_complaints
    cts_by_period = df_complaints_.groupby('Completed ' + interval).size().reindex(ALL_PERIODS[interval], fill_value=0)
    cts_le60_by_period = df_complaints_[df_complaints_['# Days Open'] <= 60].groupby('Completed ' + interval).size().reindex(ALL_PERIODS[interval], fill_value=0)
    commitment = cts_le60_by_period / cts_by_period.replace(0, np.nan) * 100
    
    return commitment


df_complaints = read_complaints()
    

if __name__ == '__main__':    
    st.title('Complaints')
    show_data_srcs('Complaints', df_complaints if isinstance(df_complaints, str) else None)
    if not isinstance(df_complaints, str):
        plots = []
        
        all_devices = sorted(df_complaints['Device Type'].unique(), key=lambda dev: (dev == 'N/A', dev))
        device = st.selectbox('Select Device', all_devices, key='device')
        filtered_df_complaints_device = df_complaints[df_complaints['Device Type'] == device]
        interval = render_interval_filter(PAGE_NAME)
        min_period = filtered_df_complaints_device[list(DATE_COLS['Complaint'])].min().min().to_period(interval[0])
        start, end = render_period_filter(PAGE_NAME, interval, min_period)

        complaint_cts = compute_complaint_cts()[interval]
        for col in DATE_COLS['Complaint']:
            total_cts, cts_by_status = complaint_cts[col]
            plot = plot_bar(
                PAGE_NAME,
                total_cts,
                grouped_data=cts_by_status,
                no_data_msg='No ' + ('non-device' if device == 'N/A' else device) + (' complaint investigations were completed' if col == 'Investigation Completed Date' else ' complaints were ' + DATE_COLS['Complaint'][col].lower()) + (' in ' + period_str(start, interval) if start == end else ' between ' + period_str(start, interval) + ' and ' + period_str(end, interval)) + '.',
                bar_kwargs={'stacked': True, 'colormap': create_shifted_cmap('tab10', 4)},
                trendline_color=PROD_COLORS[device],
                min_period=min_period, 
                min_period_msg=' as Rad did not implement the current complaint process until partway through the ' + interval.lower(), 
                max_period_msg=' as there may be more ' + ('complaint investigations completed' if col == 'Investigation Completed Date' else 'complaints ' + DATE_COLS['Complaint'][col].lower()) + ' this ' + interval.lower(), 
                clip_min=0,
                rolling_avg_color=PROD_COLORS[device],
                title='# Complaint Investigations Completed' if col == 'Investigation Completed Date' else '# Complaints ' + DATE_COLS['Complaint'][col],
                y_label='# complaints',
                y_integer=True
            )
            if plot is not None:
                plots.append(plot[0])

        if device != 'N/A':
            complaint_pct_ratio = compute_complaint_pct_ratio()
            if complaint_pct_ratio is None:
                st.write('Cannot compute complaint percentage or complaint ratio as there is no usage data ' + ('during ' + period_str(start, interval) if start == end else 'between ' + period_str(start, interval) + ' and ' + period_str(end, interval)) + '.')
            else:
                complaint_pct, complaint_ratio, pct_ratio_start, msgs = complaint_pct_ratio
                plot = plot_bar(
                    PAGE_NAME,
                    complaint_pct, 
                    start=pct_ratio_start.asfreq(interval[0]),
                    bar_kwargs={'color': PROD_COLORS[device]},
                    trendline_color=PROD_COLORS[device],
                    rolling_avg_color=PROD_COLORS[device],
                    msgs=[msgs[0]],
                    max_period_msg=' as there may be more complaints and usage this ' + interval.lower(), 
                    clip_min=0, 
                    clip_max=100,
                    title='Opened Complaints as % of Usage',
                    y_label='% complaints'
                )
                if plot is not None:
                    plots.append(plot[0])
                plot = plot_bar(
                    PAGE_NAME,
                    complaint_ratio, 
                    start=pct_ratio_start.asfreq(interval[0]),
                    bar_kwargs={'color': PROD_COLORS[device]},
                    trendline_color=PROD_COLORS[device],
                    rolling_avg_color=PROD_COLORS[device],
                    msgs=[msgs[1]],
                    max_period_msg=' as there may be more complaints and usage this ' + interval.lower(), 
                    clip_min=0, 
                    clip_max=100,
                    title='Avg # Complaints per Account',
                    y_label='# complaints'
                )
                if plot is not None:
                    plots.append(plot[0])

        plot = plot_bar(
            PAGE_NAME,
            compute_complaint_commitment(interval),
            bar_kwargs={'color': PROD_COLORS[device]},
            max_period_msg=' as there may be more complaints closed this ' + interval.lower(), 
            trendline_color=PROD_COLORS[device],
            rolling_avg_color=PROD_COLORS[device],
            is_pct=True,
            title='Complaint Commitment',
            x_label='Closure ' + interval,
            y_label='% complaints open ≤60d',
            label_missing='No complaints received'
        )
        if plot is not None:
            plots.append(plot[0])
        
        responsive_columns(plots)
