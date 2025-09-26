import os
from typing import Optional

import pandas as pd
import streamlit as st

from read_data.read_audits import read_audit_data
from utils import compute_cts, create_shifted_cmap, init_page, show_data_srcs
from utils.constants import PROD_COLORS
from utils.plotting import plot_bar, responsive_columns
from utils.filters import render_breakdown_fixed, render_interval_filter, render_period_filter, render_toggle
from utils.settings import get_settings
from utils.text_fmt import period_str


if __name__ == '__main__':
    init_page('Audits')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]


def compute_audit_commitment(
    interval: str = 'Month', 
    filter_by_type: bool = True
) -> Optional[pd.Series]:
    """
    Computes the audit commitment percentage over time.

    The audit commitment is defined as the percentage of audits that were started
    in the same period as planned. Only audits of user-selected types are included 
    if `filter_by_type` is True.

    Parameters
    ----------
    interval (Optional[str]): Time interval to compute commitment ('Month', 'Quarter', 'Year').
        Defaults to 'Month'.
    filter_by_type (Optional[bool]): If True, only considers audits of user-selected types. 
        Defaults to True.

    Returns
    -------
    Optional[pd.Series]
        Series indexed by period (`Planned Start <interval>`), containing the
        commitment percentage. Periods with zero planned audits are `NaN`.
        Returns None if `df_audits` is not available (e.g., is a string placeholder).
    """
    if isinstance(df_audits, str):
        return None

    df_audits_ = df_audits if not filter_by_type else filtered_df_audits
    df_audits_ = df_audits_.copy()

    planned_col = 'Planned Start ' + interval
    start_col = 'Start ' + interval

    df_audits_['match'] = df_audits_[planned_col] == df_audits_[start_col]
    commitment = df_audits_.groupby(planned_col)['match'].mean() * 100

    return commitment


df_audits = read_audit_data()


if __name__ == '__main__':
    st.title('Audits')
    show_data_srcs('Audits', df_audits if isinstance(df_audits, str) else None)

    if not isinstance(df_audits, str):
        settings = get_settings()
        page = settings.get_page(PAGE_NAME)
        
        render_toggle()
        interval = render_interval_filter(PAGE_NAME)
        min_period = df_audits['Start ' + interval].min()
        min_period_str = period_str(min_period, interval)
        start, end = render_period_filter(PAGE_NAME, interval, min_period)
        filtered_df_audits = render_breakdown_fixed(PAGE_NAME, df_audits)
        
        audit_cts = compute_cts(PAGE_NAME, filtered_df_audits)

        period_string = period_str(start, interval) if start == end else 'between ' + period_str(start, interval) + ' and ' + period_str(end, interval)
        to_display = []
        plot = plot_bar(
            PAGE_NAME,
            audit_cts['Start Date'][0],
            grouped_data=audit_cts['Start Date'][1],
            bar_kwargs={'stacked': True, 'colormap': create_shifted_cmap('tab10', 4)},
            max_period_msg=' as there may be more audits completed this ' + interval.lower(), 
            clip_min=0,
            title='Completed Audits',
            y_label='# Audits',
            y_integer=True,
            missing_as_zero=True,
            no_data_msg='No audits matching your filters were started ' + period_string + '.'
        )
        to_display.append(plot[0])
        plot = plot_bar(
            PAGE_NAME,
            compute_audit_commitment(interval),
            bar_kwargs={'color': PROD_COLORS['N/A'], 'label': '_nolegend_'},
            tol_lower=100,
            min_period_msg=f' as there are no records of audits before this {interval.lower()}',
            max_period_msg=f' as there may be more audits completed this {interval.lower()}',
            is_pct=True,
            title='Audit Commitment',
            y_label='% planned audits completed',
            label_missing='No planned audits',
            no_data_msg='No audits matching your filters were planned for ' + period_string + ', so cannot plot audit commitment.'
        )
        to_display.append(plot[0])
        responsive_columns(to_display)
