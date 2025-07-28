import pandas as pd
import streamlit as st

from utils import ALL_PERIODS, PROD_COLORS
from utils.filters import render_interval_filter, render_period_filter
from utils.read_data import read_aes
from utils.plotting import plot_bar
from utils.text_fmt import period_str


@ st.cache_data
def compute_ae_cts():
    """
    Computes counts of AEs received per month and quarter.

    Groups the `df_aes` DataFrame by the received date column at both monthly and quarterly intervals,
    then counts the number of AEs per period. Missing periods are filled with 0.

    Returns
    -------
    dict[str, pd.Series]
        A dictionary with keys 'Month' and 'Quarter'. Each value is a Series indexed by period 
        (month or quarter), with values representing the number of AEs received in that period.

    Example
    -------
    >>> compute_ae_cts()
    {
        'Month': 
        2024-01    3
        2024-02    5
        2024-03    2
        Freq: M, dtype: int64,

        'Quarter': 
        2024Q1    10
        Freq: Q-DEC, dtype: int64
    }
    """
    ae_cts = {}
    for interval_, periods in ALL_PERIODS.items():
       ae_cts[interval_] = df_aes.groupby(interval_ + ' Received').size().reindex(periods, fill_value=0)
    
    return ae_cts
     

if __name__ == '__main__':
    st.title('Adverse Events')
    interval = render_interval_filter()
    df_aes = read_aes()
    render_period_filter()
    start, end = st.session_state[interval + '_start_period'], st.session_state[interval + '_end_period']
    ae_cts = compute_ae_cts()[interval]
    plot = plot_bar(
        ae_cts, 
        no_data_msg='No AEs were received by the FDA ' + ('during ' + period_str(start, interval) if start == end else 'between ' + period_str(start, interval) + ' and ' + period_str(end, interval)) + '.',
        bar_kwargs={'color': PROD_COLORS['N/A'], 'label': '_nolegend_'}, 
        min_period_msg=' as Rad was not incorporated until until partway through the ' + interval.lower(), 
        max_period_msg=' as there may be more AEs this ' + interval.lower(), 
        clip_min=0, 
        clip_max=100,
        title='Adverse Events',
        y_label='# AEs',
        y_integer=True
    )
    if plot is not None:
        st.pyplot(plot[0])
