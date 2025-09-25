from typing import Any, Optional, List, Tuple

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import textwrap

from utils import compute_trendline
from utils.constants import ALL_PERIODS, RAD_COLOR
from utils.settings import get_settings
from utils.text_fmt import items_in_a_series, period_str


def plot_bar(
    page_name: str,
    data: pd.Series,
    grouped_data: Optional[pd.DataFrame] = None,
    trendline: bool = True,
    rolling_avg: bool = True,
    **kwargs: Any
) -> Optional[Tuple[plt.Figure, plt.Axes]]:
    """
    Plots a bar chart with optional trendline, rolling average, and tolerance shading.

    Supports:
    - Grouped bar data (stacked bars by category)
    - Linear trendline estimation with optional prediction before/after the interval
    - Rolling average overlay (3-period by default)
    - Quality goal tolerance shading (green region for acceptable ranges)
    - Optional markers for missing values
    - Contextual annotations and axis formatting

    Parameters:
        page_name (str): Unique identifier for the page.
        data (pd.Series): Time-indexed (PeriodIndex) series of values to plot.
        grouped_data (Optional[pd.DataFrame]): If provided, used instead of `data` for grouped/stacked bars.
        trendline (bool): Whether to overlay a dashed linear trendline. Defaults to True.
        rolling_avg (bool): Whether to overlay a rolling average line. Defaults to True.
        **kwargs: Additional configuration options:
            - interval (str): Time interval (value from INTERVALS).
            - start (Period): Start of plotting range.
            - end (Period): End of plotting range.
            - min_period, max_period (Period): Full data extent (for reindexing).
            - bar_kwargs (dict): Extra kwargs for `DataFrame.plot(kind='bar', ...)`.
            - x_label (str): X-axis label.
            - y_label (str): Y-axis label.
            - title (str): Plot title.
            - y_integer (bool): Force integer y-axis ticks.
            - is_pct (bool): If True, y-axis represents percentages (0–100).
            - clip_min, clip_max (float): Bounds to clip trendline predictions.
            - tol_lower, tol_upper (float): Lower/upper bounds for green-shaded tolerance area.
            - trendline_color (str): Color for trendline.
            - rolling_avg_color (str): Color for rolling average line.
            - msgs (List[str]): Footnote-style messages annotated below the plot.
            - min_period_msg, max_period_msg (str): Notes if first/last periods are excluded from trendline.
            - label_missing (str): Legend entry for missing-value markers.
            - missing_as_zero (bool): Fill missing periods with zero if True.

    Returns:
        Optional[Tuple[plt.Figure, plt.Axes]]: Figure and axes objects of the plot,
        or None if no data is available to plot.
    """
    settings = get_settings()
    page = settings.get_page(page_name)
    interval = page.interval
    
    start = kwargs.get('start', page.get_period(interval)[0])
    end = kwargs.get('end', page.get_period(interval)[1])
    
    min_period = kwargs.get('min_period', ALL_PERIODS[interval][0])
    max_period = kwargs.get('max_period', ALL_PERIODS[interval][-1])
    all_periods_all = pd.period_range(start=min_period, end=max_period, freq=interval[0])
    data = data.reindex(all_periods_all)
    
    if kwargs.get('missing_as_zero', False):
        data = data.fillna(0)
   
    filtered_data = data[start:end]
    if filtered_data.eq(0).all() or filtered_data.isna().all():
        return

    fig, ax = plt.subplots()
    msgs = kwargs.get('msgs', [])
    all_periods = pd.period_range(start=start, end=end, freq=interval[0])
    x_labels = [period_str(period, interval) for period in all_periods]

    if grouped_data is None:
        bar_data = data
    else:
        grouped_data = grouped_data.reindex(ALL_PERIODS[interval], fill_value=0)
        bar_data = grouped_data

    filtered_bar_data = bar_data[start:end].copy().fillna(0)
    filtered_bar_data.plot(kind='bar', ax=ax, alpha=0.7, **kwargs.get('bar_kwargs', {'stacked': True}))

    is_pct = kwargs.get('is_pct', False)
        
    if trendline and not filtered_data.isna().all():
        y_values = filtered_data.copy()
        pred_before = pred_after = 0
        trendline_msgs = []
        if 'min_period_msg' in kwargs and start == min_period:
            trendline_msgs.append(period_str(min_period, interval) + kwargs['min_period_msg'])
            y_values = y_values[1:]
            pred_before = 1
        if 'max_period_msg' in kwargs and end == max_period:
            trendline_msgs.append(period_str(max_period, interval) + kwargs['max_period_msg'])
            y_values = y_values[:-1]
            pred_after = 1
        if len(y_values) > 2:
            clip_min, clip_max = kwargs.get('clip_min', 0 if is_pct else None), kwargs.get('clip_max', 100 if is_pct else None)
            y_pred = compute_trendline(y_values, pred_before, pred_after, clip_min, clip_max)
            trend_color = kwargs.get('trendline_color', RAD_COLOR)
            ax.plot(x_labels, y_pred, linestyle='dashed', color=trend_color,
                    alpha=0.7, label='Trend' if not trendline_msgs else 'Trend*')
            if trendline_msgs:
                msgs.append('*Trendline calculation excludes ' + items_in_a_series(trendline_msgs, comma_for_clarity=True) + '.')
            y_lim = max(y_pred.max(), filtered_data.max())
        else:
            y_lim = filtered_data.max() 
            
    if rolling_avg:
        rolling_avg_color = kwargs.get('rolling_avg_color', RAD_COLOR)
        rolling_avg = data.rolling(window=3, min_periods=3).mean()[start:].dropna()
        if end == max_period:
            rolling_avg = rolling_avg[:end - 1]
        else:
            rolling_avg = rolling_avg[:end]
        if len(rolling_avg) != 0:
            x_vals = [period_str(period, interval) for period in rolling_avg.index]
            ax.plot(x_vals, rolling_avg, linestyle='-', color=rolling_avg_color,
                    label='Three-' + interval.lower() + ' rolling average')
            ax.scatter(x_vals, rolling_avg, color=rolling_avg_color, s=10, alpha=0.7, label='_nolegend_')
            y_lim = max(y_lim, rolling_avg.max())
    
    if is_pct:
        y_lim = 100    
        
    if 'tol_lower' in kwargs or 'tol_upper' in kwargs:
        tol_lower = kwargs.get('tol_lower', 0)
        tol_upper = kwargs.get('tol_upper', y_lim)
        ax.axhspan(tol_lower, tol_upper, color='green', alpha=0.5, label='Quality goal')
        hline_args = {'color': 'green', 'linestyle': '--', 'linewidth': 1}
        if tol_lower:
            ax.axhline(y=tol_lower, **hline_args)
        if tol_upper:
            ax.axhline(y=tol_upper, **hline_args)
            
    if 'label_missing' in kwargs:
        na_labels = [label for label, is_na in zip(x_labels, bar_data[start:end].isna()) if is_na]
        ax.plot(na_labels, [y_lim * 0.01] * len(na_labels),
                marker='_', color='black', linestyle='None', markeredgewidth=1.5,
                label=kwargs['label_missing'])
        
    ax.set_xlabel(kwargs.get('x_label', interval))
    x_positions = range(len(filtered_data))
    ax.set_xlim(x_positions[0] - 0.5, x_positions[-1] + 0.5)
    tick_indices = np.linspace(0, len(x_labels) - 1, 10, dtype=int)
    ax.set_xticks(tick_indices)
    ax.set_xticklabels([x_labels[i] for i in tick_indices], rotation=90)
    
    ax.set_ylabel(kwargs.get('y_label'))
    ax.set_ylim(-0.025 * y_lim, 1.025 * y_lim)
    ax.ticklabel_format(style='plain', axis='y')
    if kwargs.get('y_integer'):
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_title(kwargs.get('title'))
    
    if ax.get_legend_handles_labels():
        ax.legend(loc='upper right')
    
    msg_y = -0.15
    for msg in msgs: 
        fig.text(0, msg_y, textwrap.fill(msg, width=100), ha='left', fontsize=8)
        msg_y -= 0.075
        
    return fig, ax


def sync_window_width() -> None:
    """
    Injects JavaScript to detect the browser width and store it in `st.session_state['window_width']`.

    This ensures Streamlit can adapt layouts dynamically based on window width.
    Also hides empty iframe gaps using a small style adjustment.

    Returns:
        None
    """
    components.html(
        """
        <script>
        function sendWidth() {
            const width = window.innerWidth;
            window.parent.postMessage(
                {isStreamlitMessage: true, type: "streamlit:setComponentValue", value: width},
                "*"
            );
        }
        window.addEventListener("resize", sendWidth);
        sendWidth();

        var hide_me_list = window.parent.document.querySelectorAll('iframe');
        for (let i = 0; i < hide_me_list.length; i++) { 
            if (hide_me_list[i].height == 0) {
                hide_me_list[i].parentNode.style.height = 0;
                hide_me_list[i].parentNode.style.marginBottom = '-1rem';
            }
        }
        </script>
        """,
        height=0,
    )

    if 'component_value' in st.session_state:
        st.session_state['window_width'] = st.session_state['component_value']


def responsive_columns(
    items: Optional[List[Any]] = None,
    threshold: float = 700,
    ncols: int = 2
) -> List[st.delta_generator.DeltaGenerator]:
    """
    Creates a responsive column layout in Streamlit and optionally renders items into it.

    - If the browser width is wider than `threshold`, creates `ncols` columns; otherwise a single column.
    - If `items` is provided, they are automatically distributed across the columns:
        - matplotlib Figure objects are rendered with `st.pyplot`.
        - Callable objects are invoked inside the column.
        - Other values are passed to `st.write`.
        - None values are ignored.

    Parameters
    ----------
    items : Optional[List[Any]]
        List of items to render.
    threshold : float, default 700
        Pixel width threshold to switch layouts.
    ncols : int, default 2
        Number of columns when width > threshold.

    Returns
    -------
    List[st.delta_generator.DeltaGenerator]
        List of Streamlit column (or container) objects created.
    """
    items = [item for item in (items or []) if item is not None]

    sync_window_width()
    width = st.session_state.get('window_width', 800)

    if width > threshold and len(items) > 1:
        cols = st.columns(ncols)
    else:
        cols = [st.container()]

    for i, item in enumerate(items):
        col = cols[i % len(cols)]
        with col:
            if isinstance(item, plt.Figure):
                st.pyplot(item, bbox_inches='tight')
            elif callable(item):
                item()
            else:
                st.write(item)

    return cols
