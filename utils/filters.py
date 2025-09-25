from typing import Callable, Optional, Tuple

import pandas as pd
import streamlit as st

from utils.constants import ALL_PERIODS, BREAKDOWN_COLS, INTERVALS
from utils.settings import get_settings


def get_options_sorting_key(cat: str) -> Callable[[str], object]:
    """
    Returns a sorting key function for a given category.

    The key function ensures that:
      - Predefined ordering is applied for known categories (e.g., 'Priority', 'Size').
      - 'Unknown' and 'N/A' are always placed at the end, with 'Unknown' before 'N/A'.
      - Any unexpected values are placed after 'N/A'.
      - For categories without predefined ordering, lexicographic sorting is used,
        but 'Unknown' and 'N/A' are still pushed to the end.

    Parameters:
        cat (str): Name of the category for which to generate a sorting key.

    Returns:
        Callable[[str], object]: A function that takes a string value and returns a sort key.
    """
    sorting_orders = {
        'Priority': ['Lowest', 'Low', 'Medium', 'High', 'Highest'],
        'Size': ['Small', 'Medium', 'Large']
    }

    if cat in sorting_orders:
        order = sorting_orders[cat]

        def key(x: str) -> int:
            if x == 'Unknown':
                return len(order)       # put after normal values
            elif x == 'N/A':
                return len(order) + 1   # put after 'Unknown'
            try:
                return order.index(x)
            except ValueError:
                return len(order) + 2   # any unexpected value goes after 'N/A'
        return key

    # Default: lexicographic sort but push Unknown/N/A to the end
    def default_key(x: str):
        if x == 'Unknown':
            return (1, 0)
        elif x == 'N/A':
            return (1, 1)
        return (0, x)
    
    return default_key


def render_interval_filter(page_name: str, default: str = 'Month') -> str:
    """
    Displays a sidebar radio button for selecting the interval and stores the selection in Settings.

    Parameters:
        page_name (str): Name of the page for which the interval filter applies.
        default (str, optional): Default interval to use if none is set. Defaults to 'Month'.

    Returns:
        str: The selected interval for this page (e.g., 'Month', 'Quarter', 'Year').
    """
    settings = get_settings()
    page = settings.get_page(page_name)

    interval_key = f'{page_name}_interval'

    # Initialize session_state if missing
    if interval_key not in st.session_state:
        st.session_state[interval_key] = page.interval if page.interval in INTERVALS else default

    # Render radio; Streamlit manages session_state automatically
    st.sidebar.radio(
        'Interval',
        INTERVALS,
        index=INTERVALS.index(st.session_state[interval_key]),
        key=interval_key
    )

    # Sync PageState
    page.interval = st.session_state[interval_key]
    return page.interval


def render_period_filter(
    page_name: str,
    interval: Optional[str] = None,
    default_start: Optional[pd.Period] = None,
    default_end: Optional[pd.Period] = None
) -> Tuple[pd.Period, pd.Period]:
    """
    Displays a period slider for the selected interval and syncs selection to PageState.

    Returns the currently selected start and end periods.
    """
    settings = get_settings()
    page = settings.get_page(page_name)

    interval_key = f'{page_name}_interval'
    interval = interval or st.session_state.get(interval_key, page.interval)
    slider_key = f'{page_name}_period_slider_{interval}'  # unique per interval

    all_periods = ALL_PERIODS[interval]
    start_default = default_start or all_periods[0]
    end_default = default_end or all_periods[-1]
    options = pd.period_range(start=start_default, end=end_default, freq=interval[0])
    labels = options.strftime('%b %Y' if interval == 'Month'
                              else 'Q%q %Y' if interval == 'Quarter'
                              else '%Y')

    # Initialize slider value in session_state
    if slider_key not in st.session_state:
        start_period, end_period = page.get_period(interval)
        if start_period and end_period:
            start_idx = options.get_loc(start_period)
            end_idx = options.get_loc(end_period)
        else:
            start_idx, end_idx = 0, len(options) - 1
        st.session_state[slider_key] = (start_idx, end_idx)

    # Callback to sync PageState when slider changes
    def update_page_state():
        start_idx, end_idx = st.session_state[slider_key]
        page.set_period(interval, options[start_idx], options[end_idx])

    # Render the select_slider
    st.sidebar.select_slider(
        f'{interval}s',
        options=list(range(len(labels))),
        value=st.session_state[slider_key],
        format_func=lambda i: labels[i],
        key=slider_key,
        on_change=update_page_state
    )

    # Ensure PageState is up to date immediately
    start_idx, end_idx = st.session_state[slider_key]
    page.set_period(interval, options[start_idx], options[end_idx])

    return page.get_period(interval)


def render_breakdown_fixed(page_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Renders breakdown and fixed-category filters for a given page and returns filtered data.
    """
    settings = get_settings()
    page = settings.get_page(page_name)

    # Breakdown categories
    breakdown_cat_options = [c for c in BREAKDOWN_COLS[page_name] if df[c].nunique() <= 5]
    breakdown_cat_options.sort()
    breakdown_key = f'{page_name}_breakdown'

    if breakdown_key not in st.session_state:
        st.session_state[breakdown_key] = page.breakdown if page.breakdown in breakdown_cat_options else None

    # Breakdown selectbox
    st.selectbox(
        'Select category to break down by (leave as None to fix all)',
        options=[None] + breakdown_cat_options,
        index=0 if st.session_state[breakdown_key] is None
              else breakdown_cat_options.index(st.session_state[breakdown_key]) + 1,
        key=breakdown_key
    )
    page.breakdown = st.session_state[breakdown_key]

    # Fixed-category filters
    fixed_categories = [c for c in BREAKDOWN_COLS[page_name] if c != page.breakdown]

    with st.expander('Filters', expanded=True):
        for cat in fixed_categories:
            options = sorted(df[cat].dropna().unique(), key=get_options_sorting_key(cat))
            filter_key = f'{page_name}_{cat}_filter'

            if filter_key not in st.session_state:
                st.session_state[filter_key] = page.filters.get(cat, options)

            selected = st.multiselect(
                f'Select {cat} value(s)',
                options=options,
                default=st.session_state[filter_key],
                key=filter_key
            )

            if not selected:
                st.html(f'<span style="color:red;font-weight:bold;">Select at least one {cat}</span>')
                st.stop()

            page.filters[cat] = st.session_state[filter_key]

    # Apply mask
    mask = pd.Series(True, index=df.index)
    for cat in fixed_categories:
        mask &= df[cat].isin(page.filters[cat])

    return df.loc[mask]


