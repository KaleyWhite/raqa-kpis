from datetime import datetime
import time

import streamlit as st
import pandas as pd

from utils import ALL_PERIODS, RAD_DATE


def render_interval_filter():
    """
    Renders a sidebar radio button widget for selecting a time interval.

    Adds a Streamlit radio button to the sidebar allowing the user to choose 
    between 'Month' and 'Quarter' as the time aggregation interval.
    
    Returns:
        str: The selected interval, either 'Month' or 'Quarter'.
    """
    return st.sidebar.radio('Interval', ['Month', 'Quarter'], key='interval')
    
    
def render_period_filter(default_start=None, default_end=None):
    """
    Renders a Streamlit sidebar slider to select a range of time periods (months or quarters),
    starting from the date Radformation was incorporated.

    The function creates a list of period options (monthly or quarterly) based on the specified `interval`.
    It displays a slider that allows the user to select a start and end period from the available range.
    The selected periods are stored in `st.session_state['start_period']` and `st.session_state['end_period']`.

    The selection persists across multiple pages or reruns within the same user session by:
    - Initializing state only if not already set, or using provided defaults to allow different defaults per page.
    - Using the slider's `on_change` callback to update state immediately when the slider changes,
      preventing update lag or skipping every other change.

    Parameters:
        interval (str): Either 'Month' or 'Quarter'. Determines the granularity of the periods.
        default_start (pd.Period, optional): Default start period if state is not set. If None, uses earliest period.
        default_end (pd.Period, optional): Default end period if state is not set. If None, uses latest period.

    Returns:
        None
    """
    interval = st.session_state.interval
    options = ALL_PERIODS[interval]
    labels = options.strftime('%b %Y' if interval == 'Month' else 'Q%q %Y')

    # Initialize defaults only if not already set
    if interval + '_start_period' not in st.session_state:
        st.session_state[interval + '_start_period'] = default_start or options[0]
    if interval + '_end_period' not in st.session_state:
        st.session_state[interval + '_end_period'] = default_end or options[-1]

    default_value = (
        options.get_loc(st.session_state[interval + '_start_period']),
        options.get_loc(st.session_state[interval + '_end_period']),
    )

    def on_slider_change():
        start_idx, end_idx = st.session_state.period_slider
        st.session_state[interval + '_start_period'] = options[start_idx]
        st.session_state[interval + '_end_period'] = options[end_idx]

    st.sidebar.select_slider(
        interval + 's',
        options=range(len(labels)),
        value=default_value,
        format_func=lambda i: labels[i],
        key='period_slider',
        on_change=on_slider_change
    )
