import pandas as pd
import streamlit as st

from utils import ALL_PERIODS


def render_interval_filter(page_name, default='Month'):
    """
    Render a page-specific interval radio button ('Month' or 'Quarter').

    Stores the selection in st.session_state using a page-specific key.
    """
    key = f'{page_name}_interval'
    if key not in st.session_state:
        st.session_state[key] = default

    st.sidebar.radio(
        'Interval',
        options=['Month', 'Quarter'],
        key=key
    )
    return st.session_state[key]


def render_period_filter(page_name, interval='Month', default_start=None, default_end=None):
    """
    Render a page-specific period slider (start/end) for a given interval.

    Parameters:
        page_name (str): Unique identifier for the page.
        interval (str): 'Month' or 'Quarter'.
        default_start (pd.Period): Optional default start period.
        default_end (pd.Period): Optional default end period.

    Returns:
        start, end (pd.Period, pd.Period): Selected period range.
    """
    start_key = f'{page_name}_{interval}_start_period'
    end_key = f'{page_name}_{interval}_end_period'
    slider_key = f'{page_name}_period_slider'

    if default_start is None:
        default_start = ALL_PERIODS[interval][0]
    if default_end is None:
        default_end = ALL_PERIODS[interval][-1]
    all_periods = pd.period_range(start=default_start, end=default_end, freq=interval[0])
    options = all_periods
    labels = options.strftime('%b %Y' if interval == 'Month' else 'Q%q %Y')
    # Initialize defaults only if not already set
    if start_key not in st.session_state or st.session_state[start_key] < options[0]:
        st.session_state[start_key] = default_start
    if end_key not in st.session_state or st.session_state[end_key] > options[-1]:
        st.session_state[end_key] = default_end

    default_value = (
        options.get_loc(st.session_state[start_key]),
        options.get_loc(st.session_state[end_key])
    )

    def on_slider_change():
        start_idx, end_idx = st.session_state[slider_key]
        st.session_state[start_key] = options[start_idx]
        st.session_state[end_key] = options[end_idx]

    st.sidebar.select_slider(
        f'{interval}s',
        options=range(len(labels)),
        value=default_value,
        format_func=lambda i: labels[i],
        key=slider_key,
        on_change=on_slider_change
    )

    return st.session_state[start_key], st.session_state[end_key]
