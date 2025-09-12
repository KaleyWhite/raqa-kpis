import streamlit as st

from pages.Audits import compute_audit_commitment
from pages.CAPAs import compute_capa_commitment
from pages.Complaints import compute_complaint_commitment
from pages.Training import compute_training_commitment

from utils import RAD_COLOR, display_error, init_page
from utils.filters import render_interval_filter, render_period_filter
from utils.plotting import plot_bar
from utils.text_fmt import items_in_a_series


init_page('RA/QA KPIs')
PAGE_NAME = 'main'
    

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
        Optional[pd.Series]: The overall commitment score for each time period,
        or `None` if the requsite source data could not be retrieved.
    """
    commitments = {
        'audit': compute_audit_commitment(interval, False),
        'CAPA': compute_capa_commitment(interval, False), 
        'complaint': compute_complaint_commitment(interval, False), 
        'training': compute_training_commitment()
    }
    no_data_for = sorted(record_type for record_type, data in commitments.items() if data is None)
    if no_data_for:
        display_error('Cannot compute commitment because ' + items_in_a_series(no_data_for) + ' data could not be retrieved.')
        return
    return commitments['complaint'] * 0.35 + commitments['CAPA'] * 0.25 + commitments['training'] * 0.2 + commitments['audit'] * 0.2


if __name__ == '__main__':
    st.title('RA/QA KPIs')
    interval = render_interval_filter(PAGE_NAME)
    start, end = render_period_filter(PAGE_NAME, interval)
    
    st.markdown('''
                Select a page from the sidebar to begin.
                
                **Note:** Do not fear long load times, for we have mounds and mounds of data!
                ''')

    commitment = compute_commitment(interval)
    if commitment is not None:
        plot = plot_bar(
            PAGE_NAME,
            commitment,
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
