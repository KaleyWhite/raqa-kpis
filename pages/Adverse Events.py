import os
from typing import Any, Optional, Tuple

import matplotlib.figure
import streamlit as st

from read_data.read_aes import read_ae_data
from utils import compute_cts, init_page, show_data_srcs, suppress_warnings
from utils.filters import render_breakdown_fixed, render_interval_filter, render_period_filter
from utils.plotting import plot_bar, responsive_columns
from utils.settings import get_settings
from utils.text_fmt import period_str


if __name__ == '__main__':
    init_page('Adverse Events')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]
suppress_warnings()


def plot_ae_cts(ae_cts: dict, rad: bool = False) -> Optional[Tuple[matplotlib.figure.Figure, Any]]:
    """
    Plots adverse events (AEs) as a bar chart, optionally for 'Rad' or competitor datasets.

    This function wraps the `plot_bar` utility to display:
      - Grouped AE counts over time
      - Optional clipping and custom messages
      - Proper axis labels and integer y-axis ticks

    Parameters
    ----------
    ae_cts (dict): Dictionary containing AE data in the following format:
        {
            'Date Received': (pd.Series, pd.DataFrame)
        }
        - The Series (ae_cts['Date Received'][0]) is used for the main bar heights.
        - The DataFrame (ae_cts['Date Received'][1]) is used for grouped bars.
    rad (Optional[bool]): Whether to plot 'Rad' AEs (default False). Adjusts title and min_period_msg accordingly.

    Returns
    -------
    Optional[Tuple[matplotlib.figure.Figure, Any]]
        The figure and axes returned by `plot_bar`, or None if no data is available to plot.
    """
    kwargs = {
        'grouped_data': ae_cts['Date Received'][1],
        'clip_min': 0,
        'max_period_msg': f' as there may be more AEs this {interval.lower()}',
        'x_label': 'Date Received',
        'y_label': '# AEs',
        'y_integer': True
    }

    if rad:
        kwargs['title'] = 'Rad Adverse Events'
        kwargs['min_period_msg'] = (
            f' as Rad was not incorporated until partway through the {interval.lower()}'
        )
    else:
        kwargs['title'] = 'Competitor Adverse Events'

    plot = plot_bar(
        PAGE_NAME,
        ae_cts['Date Received'][0],
        **kwargs
    )

    return plot
    

if __name__ == '__main__':
    st.title(PAGE_NAME)
    df_aes = read_ae_data()
    show_data_srcs(PAGE_NAME, df_aes if isinstance(df_aes, str) else None)
    if not isinstance(df_aes, str):
        settings = get_settings()
        page = settings.get_page(PAGE_NAME)
        
        interval = render_interval_filter(PAGE_NAME)
        start, end = render_period_filter(PAGE_NAME, interval)
        filtered_df_aes = render_breakdown_fixed(PAGE_NAME, df_aes)
       
        all_ae_cts = compute_cts(PAGE_NAME, filtered_df_aes)
        rad_ae_cts = compute_cts(PAGE_NAME, filtered_df_aes[filtered_df_aes['Manufacturer'] == 'RADFORMATION'])
        non_rad_ae_cts = compute_cts(PAGE_NAME, filtered_df_aes[filtered_df_aes['Manufacturer'] != 'RADFORMATION'])
        
        period_string = 'during ' + period_str(start, interval) if start == end else 'between ' + period_str(start, interval) + ' and ' + period_str(end, interval)
        to_display = []
        
        plot = plot_ae_cts(rad_ae_cts, rad=True)
        to_display.append('No Radformation AEs matching your filters were received by the FDA ' + period_string + '. Yay!' if plot is None else plot[0])
        
        plot = plot_ae_cts(non_rad_ae_cts)
        to_display.append('No AEs about competitor products, matching your filters, were received by the FDA ' + period_string + '.' if plot is None else plot[0])
        
        responsive_columns(to_display)
