import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import textwrap

from utils import ALL_PERIODS, RAD_COLOR, RAD_DATE
from utils.calculations import compute_trendline
from utils.text_fmt import items_in_a_series, period_str


def plot_bar(page_name, data, grouped_data=None, trendline=True, rolling_avg=True, **kwargs):
    """
    Plots a bar chart with optional trendline, rolling average, and tolerance shading.

    This function visualizes a time series dataset as a bar chart, with support for:
    - Grouped bar data (stacked bars by category)
    - Trendline estimation with optional prediction before/after the interval
    - Rolling average overlay
    - Quality goal tolerance shading (highlighting acceptable value ranges)
    - Optional dashes at missing values
    - Contextual annotations and axis formatting

    Parameters:
        page_name (str): Unique identifier for the page.
        data (pd.Series): Time-indexed (`PeriodIndex`) series of values to plot.
        grouped_data (Optional[pd.DataFrame]): If provided, used instead of `data` for bar plot (for grouped categories).
        trendline (bool): Whether to overlay a dashed linear trendline. Defaults to `True`.
        rolling_avg (bool): Whether to plot a three-period rolling average. Defaults to `True`.
        **kwargs: Additional configuration options including:
            - interval (str): Time interval name (value from `INTERVALS`).
            - start (Period): Start of plotting range.
            - end (Period): End of plotting range.
            - min_period, max_period (Period): Full extent of data range (for reindexing).
            - bar_kwargs (dict): Extra keyword args passed to `DataFrame.plot(kind='bar', ...)`.
            - x_label (str): X-axis label.
            - y_label (str): Y-axis label.
            - title (str): Plot title.
            - y_integer (bool): If `True`, enforce integer y-axis ticks.
            - is_pct (bool): If `True`, y-axis is percentage (0–100); enables clipping and limits.
            - clip_min, clip_max (float): Min/max values to clip the trendline predictions.
            - tol_lower, tol_upper (float): Lower/upper bounds for green-shaded tolerance area.
            - trendline_color (str): Color for the trendline.
            - rolling_avg_color (str): Color for the rolling average line.
            - msgs (List[str]): Additional footnote-style messages to annotate below the plot.
            - min_period_msg, max_period_msg (str): Appended to trendline annotation if min/max period is not used in trendline calculation.
            - no_data_msg (str): Message shown when data in range is all zero or missing.
            - label_missing (str): Legend entry for the dashes indicating missing values. If not provided, missing values are not indicated.

    Returns:
        tuple: (matplotlib.figure.Figure, matplotlib.axes.Axes) of the constructed plot,
               or `None` if no data is available to plot.
    """
    interval = st.session_state[f'{page_name}_interval']
    
    # Plotting range
    start = kwargs.get('start', st.session_state[f'{page_name}_{interval}_start_period'])
    end = kwargs.get('end', st.session_state[f'{page_name}_{interval}_end_period'])
    
    # Total range (used to compute rolling average)
    min_period = kwargs.get('min_period', ALL_PERIODS[interval][0])
    max_period = kwargs.get('max_period', ALL_PERIODS[interval][-1])
    all_periods_all = pd.period_range(start=min_period, end=max_period, freq=interval[0])
    data = data.reindex(all_periods_all)
    
    # Only plot data in the user-specified range
    filtered_data = data[start:end]
    if filtered_data.eq(0).all():
        st.write(kwargs.get('no_data_msg', 'No data'))
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
    filtered_bar_data.plot(kind='bar', ax=ax, alpha=0.7, **kwargs.get('bar_kwargs', {}))
    
    is_pct = kwargs.get('is_pct', False)
        
    if trendline:
        min_period_msg = kwargs.get('min_period_msg', ' as Rad was not incorporated until ' + pd.to_datetime(RAD_DATE).strftime('%b %d, %Y'))
        # Extract values to fit the trendline to
        # Exclude first (`min_period`) and last (`max_period`) periods in which data is available
        y_values = filtered_data.copy()
        pred_before = pred_after = 0
        trendline_msgs = []
        if start == min_period:
            trendline_msgs.append(period_str(min_period, interval) + min_period_msg)
            y_values = y_values[1:]  # Exclude first period in which data is available
            pred_before = 1  # Instead of earliest value, extrapolate to earliest period
        if 'max_period_msg' in kwargs and end == max_period:
            trendline_msgs.append(period_str(max_period, interval) + kwargs['max_period_msg'])
            y_values = y_values[:-1]   # Exclude last period in which data is available
            pred_after = 1  # Instead of latest value, extrapolate to latest period
        if len(y_values) > 2:  # Not helpful to fit a trendline to 2 or fewer values
            clip_min, clip_max = kwargs.get('clip_min', 0 if is_pct else None), kwargs.get('clip_max', 100 if is_pct else None)
            y_pred = compute_trendline(y_values, pred_before, pred_after, clip_min, clip_max)  # Get a prediction for each period
            trend_color = kwargs.get('trendline_color', RAD_COLOR)
            ax.plot(x_labels, y_pred, linestyle='dashed', color=trend_color, alpha=0.7, label='Trend' if not trendline_msgs else 'Trend*')
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
            ax.plot(x_vals, rolling_avg, linestyle='-', color=rolling_avg_color, label='Three-' + interval.lower() + ' rolling average')
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
            
    # Indicate missing data
    if 'label_missing' in kwargs:
        na_labels = [label for label, is_na in zip(x_labels, bar_data[start:end].isna()) if is_na]
        ax.plot(
            na_labels,
            [y_lim * 0.01] * len(na_labels),
            marker='_',
            color='black',
            linestyle='None',
            markeredgewidth=1.5,
            label=kwargs['label_missing']
        )
        
    ax.set_xlabel(kwargs.get('x_label', interval))
    x_positions = range(len(filtered_data))
    ax.set_xlim(x_positions[0] - 0.5, x_positions[-1] + 0.5)  # Padding so left- and rightmost bars aren't cut off in the middle
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
        ax.legend()
    
    msg_y = -0.15
    for msg in msgs: 
        fig.text(
            0,
            msg_y,
            textwrap.fill(msg, width=100),
            ha='left',
            fontsize=8
        )
        msg_y -= 0.075
        
    return fig, ax


def sync_window_width():
    """
    Injects JavaScript to detect browser width and store it in session_state['window_width'].
    
    Returns:
        None
    """
    components.html(
        """
        <script>
        const streamlitDoc = window.parent.document;
        function sendWidth() {
            const width = window.innerWidth;
            window.parent.postMessage(
                {isStreamlitMessage: true, type: "streamlit:setComponentValue", value: width},
                "*"
            );
        }
        window.addEventListener("resize", sendWidth);
        sendWidth();
        </script>
        """,
        height=0,
    )
    if 'component_value' in st.session_state:
        st.session_state['window_width'] = st.session_state['component_value']


def responsive_columns(items=None, threshold=700, ncols=2):
    """
    Creates a responsive column layout and optionally renders items into it.

    If the browser window is wider than `threshold`, creates `ncols` columns;
    otherwise, a single column. If `items` is provided, it distributes and 
    renders them automatically.

    Parameters
    ----------
    items (Optional[List[Any]]): List of things to render. Each item can be:
        - A `matplotlib` `Figure` (will be shown with `st.pyplot`)
        - A callable (will be called inside its column)
        - Any value passed to `st.write`
        - Any None value is removed before rendering
    threshold (Optional[float]):
        Pixel width threshold to switch layouts. Default is 900.
    ncols (Optional[int]):
        Number of columns when width > threshold. Default is 2.

    Returns
    -------
    List[st.delta_generator.DeltaGenerator]:
        List of column objects
    """
    items = [item for item in items if item is not None]
    
    sync_window_width()
    width = st.session_state.get('window_width', 800)

    if width > threshold and len(items) > 1:
        cols = st.columns(ncols)
    else:
        cols = [st.container()]

    if items:
        for i, item in enumerate(items):
            col = cols[i % len(cols)]
            with col:
                if isinstance(item, plt.Figure):
                    st.pyplot(item, use_container_width=True)
                elif callable(item):
                    item()
                else:
                    st.write(item)
    return cols
