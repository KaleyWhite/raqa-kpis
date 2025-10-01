import os

import pandas as pd
import streamlit as st

from read_data.read_usage import read_usage_data
from utils import init_page, show_data_srcs
from utils.constants import ALL_PERIODS
from utils.filters import render_breakdown_fixed, render_interval_filter, render_period_filter, render_toggle
from utils.plotting import display_no_data_msg, plot_bar, responsive_columns
from utils.settings import get_settings
from utils.text_fmt import period_str


if __name__ == '__main__':
    init_page('Usage Volume')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]


if __name__ == '__main__':
    st.title('Usage Volume')
    df_usage = read_usage_data()
    show_data_srcs('Usage', df_usage if isinstance(df_usage, str) else None)
    if not isinstance(df_usage, str):
        settings = get_settings()
        page = settings.get_page(PAGE_NAME)
        
        render_toggle()
        interval = render_interval_filter(PAGE_NAME)
        min_period = df_usage['Usage ' + interval].min()
        max_period = ALL_PERIODS[interval][-1]
        start, end = render_period_filter(PAGE_NAME, min_period)
        filtered_df_usage = render_breakdown_fixed(PAGE_NAME, df_usage)
        ct_data = filtered_df_usage.groupby('Usage ' + interval)['Number Of Runs'].sum().reindex(pd.period_range(start=min_period, end=max_period, freq=interval[0]), fill_value=0)

        to_display = []
        plot = plot_bar(
            PAGE_NAME,
            ct_data, 
            release_dates=True,
            interval=interval,
            start=start,
            end=end,
            min_period=min_period, 
            max_period=max_period, 
            min_period_msg=f' as Rad did not start tracking usage data until partway through the {interval.lower()}', 
            max_period_msg=f' as we don\'t yet have all data for this {interval.lower()}',
            clip_min=0,
            title='Usage Volume',
            no_data_msg='No usage matching your criteria occurred' + (' during ' + period_str(start, interval) if start == end else ' between ' + period_str(start, interval) + ' and ' + period_str(end, interval)) + '.',
            omit_legend_entries=['Number Of Runs']
        )
        to_display.append(plot[0])
            
        responsive_columns(to_display)
