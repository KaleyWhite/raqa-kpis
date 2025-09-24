import random
from typing import Dict, List, Optional, Sequence, Tuple
import warnings

from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import streamlit as st

from utils.constants import ALL_PERIODS, DATE_COLS, SRCS
from utils.settings import get_settings

pd.set_option('future.no_silent_downcasting', True)
warnings.filterwarnings(
    'ignore',
    message=r".*was created with a default value but also had its value set via the Session State API.*",
)


def compute_bin_width(data_series_list: List[pd.Series]) -> float:
    """
    Computes a common histogram bin width using the Freedman-Diaconis rule for a list of numeric series.

    Parameters
    ----------
    data_series_list (List[pd.Series]): List of pandas Series containing numeric data.

    Returns
    -------
    float:
        Bin width to use across all series. Returns at least 1 as a fallback if data is insufficient.
    """
    # Concatenate all series to compute global IQR
    all_data = np.concatenate([s.dropna().to_numpy() for s in data_series_list])
    if len(all_data) < 2:
        return 1  # fallback if not enough data

    q75, q25 = np.percentile(all_data, [75, 25])
    iqr = q75 - q25
    bin_width = 2 * iqr / (len(all_data) ** (1/3))
    return max(bin_width, 1)  # ensure at least 1


def compute_cts(src: str, filtered_df: pd.DataFrame) -> Dict[str, Tuple[pd.Series, pd.DataFrame]]:
    """
    Computes counts of records for a given time interval, optionally broken down by a category.

    For the specified interval (e.g., 'Month', 'Quarter', 'Year') and each date column in DATE_COLS[src]:
        - Computes total counts per period.
        - Computes counts per period broken down by the specified st.session_state[breakdown_category].

    Parameters:
        src (str): Key identifying the source dataset in DATE_COLS.
        filtered_df (pd.DataFrame): DataFrame containing the filtered records to count.

    Returns:
        Dict[str, Tuple[pd.Series, pd.DataFrame]]:
            Dictionary keyed by date column, where each value is a tuple:
            - total_counts (pd.Series): Total counts per period (index = period, values = count).
            - counts_by_category (pd.DataFrame): Counts per period broken down by the breakdown category
              (index = period, columns = unique values of the breakdown category).

    Example:
        >>> ticket_cts = compute_cts('Development Tickets', filtered_ticket_df)
        >>> ticket_cts['Date Created'][0]  # Total tickets created each month
        2024-01    2
        2024-02    5
        2024-03    3
        Freq: M, dtype: int64

        >>> ticket_cts['Date Created'][1]  # Tickets created by device
                  Device A  Device B
        2024-01        1         1
        2024-02        4         1
        2024-03        3         0
    """
    cts: Dict[str, Tuple[pd.Series, pd.DataFrame]] = {}
    page = get_settings().get_page(src)
    interval, breakdown_category = page.interval, page.breakdown

    for col in DATE_COLS[src]:
        period_col = col.replace('Date', interval)  # E.g., "Date Created" -> "Month Created"

        # Total counts per period
        total_cts = filtered_df.groupby(period_col).size().reindex(ALL_PERIODS[interval], fill_value=0)

        if breakdown_category is None:
            cts[col] = (total_cts, total_cts)
        else:
            # Counts broken down by category
            cts_by_selection = (
                filtered_df.groupby([period_col, breakdown_category])
                .size()
                .unstack(fill_value=0)
                .reindex(ALL_PERIODS[interval], fill_value=0)
            )
            cts[col] = (total_cts, cts_by_selection)

    return cts


def compute_trendline(
    y_values: Sequence[float],
    pred_before: int = 0,
    pred_after: int = 0,
    clip_min: Optional[float] = None,
    clip_max: Optional[float] = None
) -> np.ndarray:
    """
    Computes a linear trendline for the given data with optional prediction padding and clipping.

    Fits a linear model y = a * x + b to non-NaN values in y_values using constrained optimization,
    where the intercept b is constrained to be non-negative (b ≥ 0). Optionally predicts values 
    for periods before and after the input data, and clips predicted values to specified bounds.

    Parameters:
        y_values (Sequence[float]): Sequence of numeric values (may contain NaNs).
        pred_before (int, optional): Number of periods to predict before the input data. Defaults to 0.
        pred_after (int, optional): Number of periods to predict after the input data. Defaults to 0.
        clip_min (Optional[float], optional): Minimum value to clip predictions to. Defaults to None.
        clip_max (Optional[float], optional): Maximum value to clip predictions to. Defaults to None.

    Returns:
        np.ndarray: Predicted trendline values including any before/after extrapolation and clipping.
    """
    period_nos = np.arange(len(y_values))
    mask = ~pd.isna(y_values)
    x, y = period_nos[mask], np.array(y_values)[mask]

    def loss(params):
        a, b = params
        y_pred = a * x + b
        return np.mean((y - y_pred) ** 2)

    constraints = [{'type': 'ineq', 'fun': lambda params: params[1]}]  # b ≥ 0
    res = minimize(loss, x0=[1.0, 0.0], constraints=constraints)

    a, b = res.x
    to_pred = np.concatenate([
        np.arange(-pred_before, 0),
        period_nos,
        np.arange(len(period_nos), len(period_nos) + pred_after)
    ])
    y_pred = a * to_pred + b

    if clip_min is not None or clip_max is not None:
        y_pred = np.clip(y_pred, clip_min, clip_max)

    return y_pred


def create_shifted_cmap(cmap_name: str, shift: Optional[int] = None) -> ListedColormap:
    """
    Returns a new ListedColormap based on a shifted version of a named colormap.

    This function takes a named Matplotlib colormap (e.g., 'tab10') and rotates its list of colors 
    by the specified amount. If `shift` is not provided, a random shift is applied.

    Parameters:
        cmap_name (str): Name of a discrete colormap available in Matplotlib.
        shift (Optional[int]): Number of colors to rotate the colormap by. 
                               If None, a random shift between 1 and (N-1) is used,
                               where N is the number of colors in the colormap.

    Returns:
        ListedColormap: A new colormap with colors rotated from the original.

    Example:
        >>> shifted_cmap = create_shifted_cmap('tab10', shift=3)
        >>> plt.bar(range(10), [1] * 10, color=[shifted_cmap(i) for i in range(10)])
    """
    cmap = plt.get_cmap(cmap_name)
    colors = cmap.colors
    if shift is None:
        shift = random.randint(1, len(colors) - 1)
    shifted_colors = colors[shift:] + colors[:shift]
    return ListedColormap(shifted_colors)


def init_page(pg_title: str) -> None:
    """
    Safely initializes the Streamlit page configuration.

    Ensures that st.set_page_config is called only once per page
    and always before any other Streamlit commands. This avoids
    the StreamlitSetPageConfigMustBeFirstCommandError that occurs
    when multiple imports or reruns cause duplicate calls.

    Behavior:
        - Sets the page title to pg_title and layout to 'wide'.
        - Uses st.session_state['page_configured'] as a flag to 
          prevent multiple calls within the same page.

    Parameters:
        pg_title (str): Title to display for the Streamlit page.

    Returns:
        None
    """
    if 'page_configured' not in st.session_state:
        try:
            st.set_page_config(page_title=pg_title, layout='wide')
            st.session_state['page_configured'] = True
        except Exception as e:
            st.write(e)


def show_data_srcs(pg_title: str = 'RA/QA KPIs', error_msg: Optional[str] = None) -> None:
    """
    Displays a collapsible "Data Sources" expander on the Streamlit page.

    The expander shows the data source(s) relevant to the given page.  
    If an error message is provided, the expander defaults to expanded, 
    uses a red ❌ icon instead of ℹ️, and displays the error message in bold red text.

    Parameters:
        pg_title (str, optional): 
            The title of the page whose data sources should be displayed. 
            Defaults to 'RA/QA KPIs'. Uses a global SRCS mapping to 
            resolve page-specific data source information.
        error_msg (Optional[str], optional): 
            If provided, overrides the default ℹ️ icon with ❌, expands 
            the expander by default, and appends the error message in 
            highlighted red text below the data sources. Defaults to None.

    Returns:
        None
    """
    icon = '❌' if error_msg else 'ℹ️'
    with st.expander(icon + ' Data Sources', expanded=bool(error_msg)):
        if pg_title == 'RA/QA KPIs':
            html = '<br>'.join(f'<strong>{pg}:</strong> {src[0]}' for pg, src in SRCS.items())
        else:
            html = SRCS[pg_title][1]
        if error_msg:
            html += f'<br><br><span style="color:red;font-weight:bold;">{error_msg}</span>'
        st.html(html)
      