from typing import Optional, Tuple

import pandas as pd
import streamlit as st

from utils.constants import ALL_PERIODS, BREAKDOWN_COLS, INTERVALS
from utils.settings import get_settings


def get_options_sorting_key(cat):
    sorting_orders = {
        'Priority': ['Lowest', 'Low', 'Medium', 'High', 'Highest'],
        'Size': ['Small', 'Medium', 'Large']
    }
    if cat in sorting_orders:
        return lambda x: sorting_orders[cat].index(x)
    return lambda x: x


def render_interval_filter(page_name: str, default: str = 'Month') -> str:
    """
    Displays a sidebar radio button for selecting the interval and stores the selection in Settings.

    The selected interval is persisted in both:
      1. Streamlit session state (`st.session_state`) for cross-page persistence.
      2. The `PageState` object in the centralized `Settings` object.

    Parameters:
        page_name (str): Name of the page for which the interval filter applies.
        default (str, optional): Default interval to use if none is set. Defaults to 'Month'.

    Returns:
        str: The selected interval for this page (e.g., 'Month', 'Quarter', 'Year').
    """
    settings = get_settings()
    page = settings.get_page(page_name)

    interval_key = f'{page_name}_interval'

    # Initialize session state if not already set
    if interval_key not in st.session_state:
        st.session_state[interval_key] = page.interval if page.interval in INTERVALS else default

    # Radio widget manages session_state automatically via key
    st.sidebar.radio(
        'Interval',
        INTERVALS,
        index=INTERVALS.index(st.session_state[interval_key]),
        key=interval_key
    )

    # Sync back to Settings
    page.interval = st.session_state[interval_key]

    return page.interval


def render_period_filter(page_name: str, interval: Optional[str] = None,
                         default_start: Optional[pd.Period] = None,
                         default_end: Optional[pd.Period] = None) -> Tuple[pd.Period, pd.Period]:
    settings = get_settings()
    page = settings.get_page(page_name)

    interval_key = f'{page_name}_interval'
    interval = interval or st.session_state.get(interval_key, page.interval)

    slider_key = f'{page_name}_{interval}_period_slider'

    all_periods = ALL_PERIODS[interval]
    start_default = default_start or all_periods[0]
    end_default = default_end or all_periods[-1]
    options = pd.period_range(start=start_default, end=end_default, freq=interval[0])
    labels = options.strftime('%b %Y' if interval == 'Month'
                              else 'Q%q %Y' if interval == 'Quarter'
                              else '%Y')

    # Callback to sync PageState when slider changes
    def update_page_state():
        val = st.session_state[slider_key]
        if isinstance(val, int):
            val = (val, val)
        page.set_period(interval, options[val[0]], options[val[1]])

    # Initialize session_state only if missing
    if slider_key not in st.session_state:
        start_period, end_period = page.get_period(interval)
        if start_period and end_period:
            start_idx = options.get_loc(start_period)
            end_idx = options.get_loc(end_period)
        else:
            start_idx, end_idx = 0, len(options) - 1
        st.session_state[slider_key] = (start_idx, end_idx) if len(options) > 1 else 0

    # Create the slider with the callback
    slider_value = st.sidebar.select_slider(
        f'{interval}s',
        options=list(range(len(labels))),
        value=st.session_state[slider_key],
        format_func=lambda i: labels[i],
        key=slider_key,
        on_change=update_page_state
    )

    # Return the current PageState value
    return page.get_period(interval)


def render_breakdown_fixed(page_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Renders breakdown and fixed-category filters for a given page, storing selections in Settings.

    Selections are persisted in PageState and Streamlit session_state.
    Fixed-category filters respond immediately on first selection.

    Parameters:
        page_name (str): Name of the page for which to render the breakdown and filters.
        df (pd.DataFrame): DataFrame containing the data to filter.

    Returns:
        pd.DataFrame: Filtered DataFrame based on the fixed-category filters.
    """
    settings = get_settings()
    page = settings.get_page(page_name)

    # Breakdown categories (only those with <=5 unique values)
    breakdown_cat_options = [c for c in BREAKDOWN_COLS[page_name] if df[c].nunique() <= 5]
    breakdown_cat_options.sort()

    breakdown_key = f'{page_name}_breakdown'

    # Initialize session_state for breakdown if not set
    if breakdown_key not in st.session_state:
        st.session_state[breakdown_key] = page.breakdown if page.breakdown in breakdown_cat_options else None

    # Breakdown selectbox (manages session_state)
    st.selectbox(
        'Select category to break down by (leave as None to fix all)',
        options=[None] + breakdown_cat_options,
        index=0 if st.session_state[breakdown_key] is None
              else breakdown_cat_options.index(st.session_state[breakdown_key]) + 1,
        key=breakdown_key
    )

    # Sync PageState after widget renders
    page.breakdown = st.session_state[breakdown_key]

    # Fixed-category filters (all other breakdown options)
    fixed_categories = [c for c in BREAKDOWN_COLS[page_name] if c != page.breakdown]

    with st.expander('Filters', expanded=True):
        for cat in fixed_categories:
            options = sorted(df[cat].dropna().unique(), key=get_options_sorting_key(cat))
            filter_key = f'{page_name}_{cat}_filter'

            # Only set default if not already in session_state
            if filter_key not in st.session_state:
                st.session_state[filter_key] = page.filters.get(cat, options)

            # Multiselect (Streamlit manages session_state automatically)
            selected = st.multiselect(
                f'Select "{cat}" value(s)',
                options=options,
                default=None if filter_key in st.session_state else st.session_state[filter_key],
                key=filter_key
            )

            if not selected:
                st.html(f'<span style="color:red;font-weight:bold;">Select at least one {cat}</span>')
                st.stop()

            # Sync PageState after widget reads its value
            page.filters[cat] = st.session_state[filter_key]

    # Apply mask to DataFrame
    mask = True
    for cat in fixed_categories:
        mask &= df[cat].isin(page.filters[cat])

    return df.loc[mask]



