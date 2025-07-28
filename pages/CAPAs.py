import streamlit as st

from utils import ALL_PERIODS, DATE_COLS
from utils.filters import render_interval_filter, render_period_filter
from utils.plotting import plot_bar
from utils.read_data import read_capas
from utils.text_fmt import items_in_a_series, period_str


@st.cache_data
def compute_capa_cts():
    """
    Computes CAPA counts by month and quarter for each CAPA-related date field,
    returning total counts and counts grouped by Problem Type.

    For each interval ('Month', 'Quarter') and CAPA date column in `DATE_COLS['CAPA']`:
        - Groups data by time period and counts total CAPAs.
        - Groups by both period and "Problem Type" to count categorized CAPAs.

    Returns:
        dict[str, dict[str, tuple[pd.Series, pd.DataFrame]]]: Nested dictionary:
            {
                'Month': {
                    'Date Created': (total_cts, cts_by_problem_type),
                    ...
                },
                'Quarter': {
                    'Date Created': (total_cts, cts_by_problem_type),
                    ...
                }
            }

    Example:
        >>> capa_cts = compute_capa_counts()
        >>> capa_cts['Month']['Date Created'][0]  # Total CAPAs opened each month
        2024-01    2
        2024-02    5
        2024-03    3
        Freq: M, dtype: int64

        >>> capa_cts['Month']['Date Created'][1]  # CAPAs opened by problem type
                  Audit Issue Customer Complaint
        2024-01       1       1
        2024-02       4       1
        2024-03       3       0
    """
    capa_cts = {}
    for interval_ in ['Month', 'Quarter']:
        capa_cts[interval_] = {}
        for col in DATE_COLS['CAPA']:
            period_col = col.replace('Date', interval)  # e.g., "Date Created" -> "Month Created"
            total_cts = filtered_df_capas_prob_types.groupby(period_col).size().reindex(ALL_PERIODS, fill_value=0)  # Overall # CAPAs opened/due/submitted/approved during the user-selected time interval
            cts_by_prob_type = filtered_df_capas_prob_types.groupby([period_col, 'Problem Type']).size().unstack().reindex(ALL_PERIODS, fill_value=0)  # # CAPAs opened/due/submitted/approved during the user-selected time interval, by type
            capa_cts[interval_][col] = (total_cts, cts_by_prob_type)
    return capa_cts


@st.cache_data
def ct_by_submission_date(interval='Month', filter_by_prob_type=True):
    """
    Counts the number of CAPAs submitted during each period in the user-selected time interval.
    Missing periods are filled with zero.
    
    Parameters:
        interval (Optional[str]): 'Month' or 'Quarter'. Defaults to 'Month'.
        filter_by_prob_type (Optiona[bool]): If `True`, only consider the CAPAs of the user-selected Problem Types. Defaults to `True`.

    Returns:
        pd.Series: A `Series` indexed by period, containing the number of CAPAs submitted in each.
    """
    df_capas_ = filtered_df_capas_prob_types if filter_by_prob_type else df_capas
    submitted = df_capas_['Date of Submission']
    by_submission_date = submitted.groupby(interval + ' of Submission').size().reindex(ALL_PERIODS, fill_value=0)  # # CAPAs submitted during each period in the interval
    
    return by_submission_date


@st.cache_data
def compute_capa_commitment(interval='Month', filter_by_prob_type=True):
    """
    Returns CAPA commitment (percent of CAPAs submitted on or before their due date) for each period in which a CAPA for one of the user-selected problem types was submitted

    Parameters:
        interval (Optional[str]): 'Month' or 'Quarter'. Defaults to 'Month'.
        filter_by_prob_type (Optiona[bool]): If `True`, only consider the CAPAs of the user-selected Problem Types. Defaults to `True`.
    
    Returns:
        pd.Series: CAPA commitment for each period, indexed by period
    """
    submitted = ct_by_submission_date(interval, filter_by_prob_type)
    ct_on_time = submitted[submitted['Due Date'] <= submitted['Date of Submission']].groupby(interval + ' of Submission').size().reindex(ALL_PERIODS, fill_value=0)  # # CAPAs submitted on time during each period in the interval
    commitment = (ct_on_time / submitted * 100).fillna(0)
    
    return commitment


@st.cache_data
def compute_capa_effectiveness(interval='Month', filter_by_prob_type=True):
    """
    Returns CAPA effectiveness (percent of CAPAs that passed effectiveness check) for each period in which a CAPA for one of the user-selected problem types was submitted

    Parameters:
        interval (Optional[str]): 'Month' or 'Quarter'. Defaults to 'Month'.
        filter_by_prob_type (Optiona[bool]): If `True`, only consider the CAPAs of the user-selected Problem Types. Defaults to `True`.
    
    Returns:
        pd.Series: CAPA effectiveness for each period, indexed by period
    """
    submitted = ct_by_submission_date(interval, filter_by_prob_type)
    ct_passed = submitted[['Effectiveness Verification Status'] == 'Pass'].groupby(interval + ' of Submission').size().reindex(ALL_PERIODS, fill_value=0)
    effectiveness = (ct_passed / submitted * 100).fillna(0)
    
    return effectiveness


df_capas = read_capas()
    
     
if __name__ == '__main__':   
    st.title('CAPAs')
    st.markdown('**Note:** CAPA stats will be provided once Kaley and Matrix support figure out the data fetch.')
    
    interval = render_interval_filter()
    all_prob_types = sorted(df_capas['Problem Type'].unique())
    prob_types = st.multiselect('Select Problem Types', options=all_prob_types, default=all_prob_types, key='prob_types')
    if not prob_types:
        st.write('Select problem type(s) to plot data')
    else:
        filtered_df_capas_prob_types = df_capas[df_capas['Problem Type'].isin(prob_types)]
        min_period = df_capas[list(DATE_COLS['CAPA'])].min(axis=1)
        render_period_filter(default_start=min_period)
        start = st.session_state[interval + '_start_period']
        end = st.session_state[interval + '_end_period']
        
        capa_cts = compute_capa_cts()[interval]
        min_period_msg = ' as Rad did not start tracking CAPAs in Matrix until partway through the ' + interval.lower()
        for col in DATE_COLS['CAPA']:
            total_cts, cts_by_prob_type = capa_cts[col]
            plot = plot_bar(
                total_cts, 
                grouped_data=cts_by_prob_type, 
                bar_kwargs={'stacked': True, 'colormap': 'tab10'},
                no_data_msg='No ' + items_in_a_series(prob_types, 'or') + ' CAPAs ' + (' during ' + period_str(start, interval) if start == end else ' between ' + period_str(start, interval) + ' and ' + period_str(end, interval)) + '.',
                min_period=min_period,
                min_period_msg=min_period_msg,
                max_period_msg=' as there may be more CAPAs ' + DATE_COLS['CAPA'][col].lower() + ' this ' + interval.lower(), 
                clip_min=0,
                title='# CAPAs ' + DATE_COLS['CAPA'][col],
                y_label='# CAPAs',
                y_integer=True
            )
            if plot is not None:
                st.pyplot(plot[0])
        commitment_effectiveness_max_period_msg = ' as there may be more CAPAs submitted this ' + interval.lower()
        plot = plot_bar(
            compute_capa_commitment(interval),
            min_period=min_period,
            min_period_msg=min_period_msg,
            max_period_msg=commitment_effectiveness_max_period_msg,
            title='% CAPAs Submitted by Due Date',
            x_label='Submission ' + interval,
            y_label='Commitment %',
            is_pct=True
        )
        if plot is not None:
            st.pyplot(plot[0])
        plot = plot_bar(
            compute_capa_effectiveness(interval),
            min_period=min_period,
            min_period_msg=min_period_msg,
            max_period_msg=commitment_effectiveness_max_period_msg,
            title='CAPA Effectiveness',
            x_label='Submission ' + interval,
            y_label='% passed effectiveness check',
            is_pct=True
        )
        if plot is not None:
            st.pyplot(plot[0])
