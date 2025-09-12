import os

import numpy as np
import streamlit as st

from utils import PROD_COLORS, create_shifted_cmap, init_page, show_data_srcs
from utils.plotting import plot_bar
from utils.filters import render_interval_filter, render_period_filter
from utils.read_data import read_audits
from utils.text_fmt import period_str


init_page('Audits')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]


@st.cache_data
def compute_audits_by_qtr(df_audits_mo):
    """
    Returns numbers of audits, grouped by quarter

    Parameters:
        df_audits_mo (pd.DataFrame): Audit counts by month

    Returns:
        pd.DataFrame: Audit counts by quarter
    """
    return df_audits_mo.groupby(['Quarter', 'Type'], as_index=False).sum(numeric_only=True)  


def compute_audit_commitment(interval='Month', filter_by_type=True):
    """
    Computes the audit commitment percentage over time.

    This function calculates the percentage of completed audits relative to the number 
    of planned audits for each time period (month or quarter).
    Only considers audits of the user-selected types.
    
    Parameters:
        interval (Optional[str]): 'Month' or 'Quarter'. Defaults to 'Month'.
        filter_by_type (Optional[bool]): If `True`, considers only the user-selected audit types.
        Defaults to `True`.

    Returns:
        Optional[pd.Series]: A `Series` indexed by period, 
        containing the audit commitment percentage values. Periods with zero planned audits 
        are returned as `NaN` to avoid division by zero.
        Returns `None` if audit data was not retrieved.
    """
    if isinstance(dfs_audits, str):
        return
    dfs_audits_ = dfs_audits if not filter_by_type else filtered_dfs_audits
    audits = dfs_audits_[interval][dfs_audits_[interval]['Planned'] != 0].groupby(interval)[['Completed', 'Planned']].sum()
    commitment = audits['Completed'] / audits['Planned'].replace(0, np.nan) * 100
    return commitment 


def plot_audit_cts():
    """
    Plots a bar chart showing the number of completed audits over time.

    This function filters audit data based on the user-selected interval and audit types,
    aggregates completed internal and/or external audits per period, and displays a 
    stacked bar chart using the `plot_bar` utility.

    If only one audit type is selected, the plot title and legend are simplified.
    A message is shown if there are no audits completed in the selected period.

    Returns:
        None. The chart is rendered directly in the Streamlit app.
    """
    completed_audits = filtered_dfs_audits[interval][[interval, 'Type', 'Completed']]
    completed_audits = completed_audits.pivot(index=interval, columns='Type', values='Completed').fillna(0)
    plot = plot_bar(
        PAGE_NAME,
        completed_audits[audit_types[0]] if len(audit_types) == 1 else completed_audits['Internal'] + completed_audits['External'],
        grouped_data=completed_audits,
        no_data_msg='No' + ('' if len(audit_types) == 2 else ' ' + audit_types[0].lower()) + ' audits were completed' + (' during ' + period_str(start, interval) if start == end else ' between ' + period_str(start, interval) + ' and ' + period_str(end, interval)) + '.',
        bar_kwargs={'stacked': True, 'colormap': create_shifted_cmap('tab10', 4)},
        max_period_msg=' as there may be more audits completed this ' + interval.lower(), 
        clip_min=0,
        title='Completed ' + ('' if len(audit_types) == 2 else audit_types[0] + ' ') + 'Audits',
        y_label='# Audits',
        y_integer=True
    )
    if plot is not None:
        fig, ax = plot
        if ax.get_legend_handles_labels():
            # Remove the unwanted legend entry
            handles, labels = ax.get_legend_handles_labels()
            filtered = [(h, l) for h, l in zip(handles, labels) if len(audit_types) != 1 or l not in ['Internal', 'External']]
            ax.legend(*zip(*filtered))  # Update legend with filtered entries
            
        st.pyplot(fig)


df_audits = read_audits()
dfs_audits = {'Month': df_audits, 'Quarter': compute_audits_by_qtr(df_audits)}


if __name__ == '__main__':
    st.title('Audits')
    show_data_srcs('Audits', df_audits if isinstance(df_audits, str) else None)

    if not isinstance(df_audits, str):
        audit_types = st.multiselect('Select Audit Types', options=['Internal', 'External'], default=['Internal', 'External'], key='audit_types')
        if not audit_types:
            st.write('Select audit type(s) to plot data')
        filtered_dfs_audits = {interval_: df_audits[df_audits['Type'].isin(audit_types)] for interval_, df_audits in dfs_audits.items()}
        interval = render_interval_filter(PAGE_NAME)
        min_period = df_audits[interval].min()
        min_period_str = period_str(min_period, interval)
        start, end = render_period_filter(PAGE_NAME, interval, min_period)
        
        plot_audit_cts()

        plot = plot_bar(
            PAGE_NAME,
            compute_audit_commitment(interval),
            no_data_msg='No' + ('' if len(audit_types) == 2 else ' ' + audit_types[0].lower()) + ' audits were planned for ' + (period_str(start, interval) if start == end else 'between ' + period_str(start, interval) + ' and ' + period_str(end, interval)) + '.',
            bar_kwargs={'color': PROD_COLORS['N/A'], 'label': '_nolegend_'},
            tol_lower=100,
            max_period_msg=' as there may be more audits completed this ' + interval.lower(),
            is_pct=True,
            title=('' if len(audit_types) == 2 else audit_types[0] + ' ') + 'Audit Commitment',
            y_label='% planned audits completed',
            label_missing='No planned audits',
        )
        
        if plot is not None:
            st.pyplot(plot[0])
