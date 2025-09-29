from typing import Callable, List, Optional, Tuple

import pandas as pd
import streamlit as st

from utils.constants import ALL_PERIODS, BREAKDOWN_COLS, INTERVALS
from utils.settings import get_settings


def get_options_sorting_key(cat: str) -> Callable[[str], object]:
    """
    Returns a sorting key function for a given category (column name).

    The key function ensures that:
      - Predefined ordering is applied for certain categories (e.g., 'Priority', 'Size') 
        for which lexicographic ordering does not make sense.
      - 'Unknown' and 'N/A' are always placed at the end, with 'Unknown' before 'N/A'.
      - For categories without predefined ordering, lexicographic sorting is used,
        but 'Unknown' and 'N/A' are still pushed to the end.

    Parameters:
        cat (str): Name of the category (DataFrame column) for which to generate a sorting key.

    Returns:
        Callable[[str], object]: A function that takes a string value and returns a sort key.
    """
    # Non-lexicographically ordered column values
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
            return order.index(x)
        return key

    # Default: lexicographic sort but push Unknown / N/A to the end
    def default_key(x: str):
        if x == 'Unknown':
            return (1, 0)
        elif x == 'N/A':
            return (1, 1)
        return (0, x)
    
    return default_key


def render_toggle(trendline=True, rolling_avg=True) -> None:
    """
    Renders "Data" (always), "Trendline" (optionally), and/or "Rolling average" (optionally) toggles in the Streamlit sidebar.
    
    Meant to be used to show/hide data, trendlines, and/or rolling average on plots.
    
    Parameters:
        trendline (bool): If True, render a toggle "Trendlines". Defaults to True.
        rolling_avg (bool): If True, render a toggle "Rolling average". Defaults to True.
    """
    with st.sidebar:
        st.toggle(
            'Data',
            value=True,
            key='data'
        )
        if trendline:
            st.toggle(
                'Trendlines',
                value=True,
                key='trendline'
            )
        if rolling_avg:
            st.toggle(
                'Rolling average',
                value=True,
                key='rolling_avg'
            )


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
    Renders breakdown selectbox and fixed-category multiselect filters for a page,
    returning the filtered DataFrame. Works for columns containing lists or strings.
    """
    settings = get_settings()
    page = settings.get_page(page_name)

    def get_unique(col):
        if len(df) == 0:
            return []
        first_val = df[col].iloc[0]
        if isinstance(first_val, list):
            return sorted({item for lst in df[col] for item in lst})
        else:
            return sorted(df[col].dropna().unique())

    # Breakdown categories
    breakdown_cat_options = [c for c in BREAKDOWN_COLS[page_name] if len(get_unique(c)) <= 5]
    breakdown_cat_options.sort()
    breakdown_key = f'{page_name}_breakdown'

    # Initialize session state only if missing
    if breakdown_key not in st.session_state or st.session_state[breakdown_key] not in breakdown_cat_options:
        st.session_state[breakdown_key] = page.breakdown if page.breakdown in breakdown_cat_options else None

    # Let Streamlit fully manage the value via key (no default/index needed)
    st.selectbox(
        'Select category to break down by (leave as None to fix all)',
        options=[None] + breakdown_cat_options,
        key=breakdown_key
    )

    page.breakdown = st.session_state[breakdown_key]

    # Fixed-category filters
    fixed_categories = [c for c in BREAKDOWN_COLS[page_name] if c != page.breakdown]
    with st.expander('Filters', expanded=True):
        for cat in fixed_categories:
            options = get_unique(cat)
            filter_key = f'{page_name}_{cat}_filter'
            # Initialize only if missing
            if filter_key not in st.session_state:
                st.session_state[filter_key] = page.filters.get(cat, options)

            # Multiselect, managed fully by session_state
            st.multiselect(
                f'Select "{cat}" value(s)',
                options=options,
                key=filter_key
            )

            page.filters[cat] = st.session_state[filter_key]

    # Apply mask
    mask = pd.Series(True, index=df.index)
    for cat in fixed_categories:
        sample_val = df[cat].iloc[0]
        if isinstance(sample_val, list):
            mask &= df[cat].apply(lambda x: any(item in page.filters[cat] for item in x))
        else:
            mask &= df[cat].isin(page.filters[cat])

    return df.loc[mask]
