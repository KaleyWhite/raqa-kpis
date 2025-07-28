import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import streamlit as st
import textwrap

from utils import ALL_PERIODS, RAD_COLOR, RAD_DATE
from utils.calculations import compute_trendline
from utils.text_fmt import items_in_a_series, period_str


def plot_bar(data, grouped_data=None, trendline=True, rolling_avg=True, **kwargs):
    """
    Plots a bar chart with optional trendline, rolling average, and tolerance shading.

    This function visualizes a time series dataset as a bar chart, with support for:
    - Grouped bar data (stacked bars by category)
    - Trendline estimation with optional prediction before/after the interval
    - Rolling average overlay
    - Quality goal tolerance shading (highlighting acceptable value ranges)
    - Contextual annotations and axis formatting

    Parameters:
        data (pd.Series): Time-indexed (`PeriodIndex`) series of values to plot.
        grouped_data (Optional[pd.DataFrame]): If provided, used instead of `data` for bar plot (for grouped categories).
        trendline (bool): Whether to overlay a dashed linear trendline. Defaults to `True`.
        rolling_avg (bool): Whether to plot a three-period rolling average. Defaults to `True`.
        **kwargs: Additional configuration options including:
            - interval (str): Time interval name ('Month' or 'Quarter').
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
            - min_period_msg, max_period_msg (str): Appended to trendline annotation if min/max period is ot used in trendline calculation.
            - no_data_msg (str): Message shown when data in range is all zero or missing.

    Returns:
        tuple: (matplotlib.figure.Figure, matplotlib.axes.Axes) of the constructed plot,
               or `None` if no data is available to plot.
    """
    #interval = kwargs.get('interval', 'Month')
    interval = st.session_state.interval
    start = kwargs.get('start', st.session_state[interval + '_start_period'])
    end = st.session_state[interval + '_end_period']
    #rad_period = pd.Period(RAD_DATE, freq=interval[0])
    #curr_period = pd.to_datetime('today').to_period(interval[0])
    min_period = kwargs.get('min_period', ALL_PERIODS[interval][0])
    max_period = kwargs.get('max_period', ALL_PERIODS[interval][-1])
    #start = kwargs.get('start', min_period)
    #end = kwargs.get('end', max_period)
    all_periods_all = pd.period_range(start=min_period, end=max_period, freq=interval[0])
    data = data.reindex(all_periods_all, fill_value=0)
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
        grouped_data = grouped_data.reindex(all_periods_all, fill_value=0)
        bar_data = grouped_data
    filtered_bar_data = bar_data[start:end]
    filtered_bar_data.plot(kind='bar', ax=ax, alpha=0.7, **kwargs.get('bar_kwargs', {}))
    
    is_pct = kwargs.get('is_pct', False)
        
    if trendline:
        min_period_msg = kwargs.get('min_period_msg', ' as Rad was not incorporated until ' + pd.to_datetime(RAD_DATE).strftime('%b %d, %Y'))
        y_values = filtered_data.values.copy()
        pred_before = pred_after = 0
        trendline_msgs = []
        if start == min_period:
            trendline_msgs.append(period_str(min_period, interval) + min_period_msg)
            y_values = y_values[1:]
            pred_before = 1
        if 'max_period_msg' in kwargs and end == max_period:
            trendline_msgs.append(period_str(max_period, interval) + kwargs['max_period_msg'])
            y_values = y_values[:-1]
            pred_after = 1
        if len(y_values) > 2:
            st.write(all_periods, data, filtered_data, y_values, pred_before, pred_after)
            clip_min, clip_max = kwargs.get('clip_min', 0 if is_pct else None), kwargs.get('clip_max', 100 if is_pct else None)
            y_pred = compute_trendline(y_values, pred_before, pred_after, clip_min, clip_max)
            trend_color = kwargs.get('trendline_color', RAD_COLOR)
            ax.plot(x_labels, y_pred, linestyle='dashed', color=trend_color, alpha=0.7, label='Trend' if not trendline_msgs else 'Trend*')
            if trendline_msgs:
                msgs.append('*Trendline calculation excludes ' + items_in_a_series(trendline_msgs, comma_for_clarity=True) + '.')
            y_lim = max(y_pred.max(), filtered_data.max())
        else:
            y_lim = filtered_data.max() 
            
    if rolling_avg:
        rolling_avg_color = kwargs.get('rolling_avg_color', RAD_COLOR)
        rolling_avg = data.rolling(window=3, min_periods=3).mean()[start:]
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
    