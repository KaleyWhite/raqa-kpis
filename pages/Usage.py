import pandas as pd
import streamlit as st

from utils import PROD_COLORS
from utils.filters import render_interval_filter, render_period_filter
from utils.plotting import plot_bar
from utils.read_data import read_usage
from utils.text_fmt import period_str


if __name__ == '__main__':
    st.title('Usage Volume')
    interval = render_interval_filter()
    df_usage = read_usage()
    devices = sorted(df_usage['Device'].unique())
    device = st.selectbox('Select Device', devices, key='device')
    df_usage_device = df_usage[df_usage['Device'] == device]
    min_period = df_usage_device[interval].min()
    max_period = pd.to_datetime('today').to_period(interval[0])
    render_period_filter(min_period)
    start = st.session_state.get('start_period')
    end = st.session_state.get('end_period')
    device_data = df_usage_device.groupby(interval)['Number Of Runs'].sum().reindex(pd.period_range(start=min_period, end=max_period, freq=interval[0]), fill_value=0)

    plot = plot_bar(
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
        min_period_msg=' as Rad did not start tracking data for ' + device + ' until partway through the ' + interval.lower(), 
        max_period_msg=' as we don\'t yet have all data for this ' + interval.lower(), 
        clip_min=0
    )
    if plot is not None:
        st.pyplot(plot[0])
