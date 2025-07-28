import pandas as pd
import streamlit as st

st.set_page_config(page_title='RA/QA KPIs', layout='wide')

from pages.Audits import compute_audit_commitment
#from pages.CAPAs import compute_capa_commitment
from pages.Complaints import compute_complaint_commitment
from pages.Training import compute_training_commitment

from utils import RAD_COLOR, RAD_DATE
from utils.filters import render_interval_filter, render_period_filter
from utils.plotting import plot_bar


def compute_commitment(interval='Month'):
    """
    Computes the overall RA/QA commitment score for a given time interval.

    This function calculates individual commitment scores for audits, CAPAs,
    complaints, and training, each weighted according to predefined importance:

        - Complaint Commitment: 35%
        - CAPA Commitment: 25%
        - Training Commitment: 20%
        - Audit Commitment: 20%

    The interval (e.g., 'Month' or 'Quarter') is used to group and compute each
    metric. The final commitment score is a weighted average of these components.

    Parameters:
        interval (Optional[str]): The time interval for computation, either 'Month' or 'Quarter'.
                        Defaults to 'Month'.

    Returns:
        pd.Series: The overall commitment score for each time period.
    """
    st.write(interval)
    audit_commitment = compute_audit_commitment(interval, False)
    #capa_commitment = compute_capa_commitment(interval, False)
    complaint_commitment = compute_complaint_commitment(interval, False)
    training_commitment = compute_training_commitment(interval, False)
    
    #return complaint_commitment * 0.35 + capa_commitment * 0.25 + training_commitment * 0.2 + audit_commitment * 0.2
    return complaint_commitment * 0.35 + training_commitment * 0.2 + audit_commitment * 0.2


if __name__ == '__main__':
    st.title('RA/QA KPIs')
    interval = render_interval_filter()
    min_period = pd.Period(RAD_DATE, freq=interval[0])
    max_period = pd.to_datetime('today').to_period(interval[0])
    render_period_filter(min_period)
    start = st.session_state.get('start_period')
    end = st.session_state.get('end_period')

    plot = plot_bar(
        compute_commitment(interval),
        interval=interval,
        start=start,
        end=end, 
        bar_kwargs={'color': RAD_COLOR},
        is_pct=True,
        title='Complaint Commitment',
        x_label='Closure ' + interval,
        y_label='% complaints open ≤60d'
    )
    if plot is not None:
        st.pyplot(plot[0])

    st.markdown('''
                Select a page from the sidebar to begin.
                
                **Note:** Do not fear long load times, for we have mounds and mounds of data!
                ''')
