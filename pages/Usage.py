import os

import pandas as pd
import streamlit as st

from utils import ALL_PERIODS, PROD_COLORS, init_page, show_data_srcs
from utils.filters import render_interval_filter, render_period_filter
from utils.plotting import plot_bar, responsive_columns
from utils.read_data import read_usage
from utils.text_fmt import period_str


if __name__ == '__main__':
    init_page('Usage Volume')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]


if __name__ == '__main__':
    st.title('Usage Volume')
    df_usage = read_usage()
    show_data_srcs('Usage', df_usage if isinstance(df_usage, str) else None)
    if not isinstance(df_usage, str):
        devices = sorted(df_usage['Device'].unique())
        device = st.selectbox('Select Device', devices, key='device')
        df_usage_device = df_usage[df_usage['Device'] == device]
        interval = render_interval_filter(PAGE_NAME)
        min_period = df_usage_device[interval].min()
        max_period = ALL_PERIODS[interval][-1]
        device_data = df_usage_device.groupby(interval)['Number Of Runs'].sum().reindex(pd.period_range(start=min_period, end=max_period, freq=interval[0]), fill_value=0)
        start, end = render_period_filter(PAGE_NAME, interval, min_period)

        plot = plot_bar(
            PAGE_NAME,
            device_data, 
            interval=interval,
            start=start,
            end=end,
            no_data_msg='No ' + device + ' usage ' + (' during ' + period_str(start, interval) if start == end else ' between ' + period_str(start, interval) + ' and ' + period_str(end, interval)) + '.',
            bar_kwargs={'color': PROD_COLORS[device]},
            trendline_color=PROD_COLORS[device],
            rolling_avg_color=PROD_COLORS[device],
            min_period=min_period, 
            max_period=max_period, 
            min_period_msg=f' as Rad did not start tracking data for {device} until partway through the {interval.lower()}', 
            max_period_msg=f' as we don\'t yet have all data for this {interval.lower()}',
            clip_min=0,
            title='Usage Volume'
        )
        if plot is not None:
            fig, ax = plot
            if ax.get_legend_handles_labels():
                # Remove the unwanted legend entry
                handles, labels = ax.get_legend_handles_labels()
                filtered = [(h, l) for h, l in zip(handles, labels) if l != 'Number Of Runs']
                ax.legend(*zip(*filtered))  # Update legend with filtered entries
            
                responsive_columns([fig])
