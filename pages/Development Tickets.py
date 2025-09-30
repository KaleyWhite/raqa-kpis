import os

import streamlit as st

from read_data.read_dev_tickets import read_dev_ticket_data
from utils import compute_cts, init_page, show_data_srcs
from utils.constants import DATE_COLS
from utils.filters import render_breakdown_fixed, render_interval_filter, render_period_filter, render_toggle
from utils.plotting import plot_bar, responsive_columns
from utils.text_fmt import period_str


if __name__ == '__main__':
    init_page('Development Tickets')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]


if __name__ == '__main__':
    st.title('Development Tickets')
    df_issues = read_dev_ticket_data()
    show_data_srcs('Development Tickets', df_issues if isinstance(df_issues, str) else None)
    if not isinstance(df_issues, str):
        render_toggle()
        interval = render_interval_filter(PAGE_NAME)
        min_period = df_issues[list(DATE_COLS['Development Tickets'])].min().min().to_period(interval[0])
        start, end = render_period_filter(PAGE_NAME, min_period)
        
        filtered_df_issues = render_breakdown_fixed('Development Tickets', df_issues)
                 
        to_display = []
        
        issue_cts = compute_cts('Development Tickets', filtered_df_issues)
        min_period_msg = ' as earlier tickets than this ' + interval.lower() + ' are not tracked in Jira'
        period_string = 'during ' + period_str(start, interval) if start == end else 'between ' + period_str(start, interval) + ' and ' + period_str(end, interval)
        for col, short in DATE_COLS['Development Tickets'].items():
            total_cts, cts_by_selection = issue_cts[col]
            plot = plot_bar(
                PAGE_NAME,
                total_cts,
                grouped_data=cts_by_selection,
                release_dates=short == 'Created',
                min_period=min_period,
                min_period_msg=min_period_msg,
                max_period_msg=' as there may be more tickets ' + short.lower() + ' this ' + interval.lower(), 
                clip_min=0,
                title='# Tickets ' + short,
                y_label='# Tickets',
                y_integer=True,
                no_data_msg=f'No tickets meeting the selected criteria were {short.lower()} {period_string}.'
            )
            to_display.append(plot[0])
        
        responsive_columns(to_display)
            