from collections import OrderedDict

from matplotlib.patches import FancyBboxPatch
import numpy as np
import streamlit as st

from pages.Audits import compute_audit_commitment
from pages.CAPAs import compute_capa_commitment
from pages.Complaints import compute_complaint_commitment
from pages.Training import compute_training_commitment

from utils import create_shifted_cmap, init_page, show_data_srcs
from utils.constants import RAD_COLOR
from utils.filters import render_interval_filter, render_period_filter
from utils.plotting import plot_bar, responsive_columns
from utils.text_fmt import items_in_a_series


if __name__ == '__main__':
    init_page('RA/QA KPIs')
PAGE_NAME = 'main'
COMMITMENT_WTS = OrderedDict([
    ('Audits', 0.2),
    ('CAPAs', 0.25),
    ('Complaints', 0.35),
    ('Training', 0.2),
])
    

def compute_commitment(interval='Month'):
    """
    Computes the overall RA/QA commitment score for a given time interval.

    This function calculates individual commitment scores for audits, CAPAs,
    complaints, and training, each weighted according to predefined importance (`COMMITMENT_WTS`)

    The interval (i.e., value from `INTERVALS`) is used to group and compute each
    metric. The final commitment score is a weighted average of these components.

    Parameters:
        interval (Optional[str]): The time interval for computation. Defaults to 'Month'.

    Returns:
        Union[Tuple[pd.Series, pd.Period, str], str]: Tuple containing:
            The overall commitment score for each time period
            The latest minimum period in any of the compueted commitments (audits, CAPAs, etc.)
            The category corresponding to that max min; 
            or an error message if the requsite source data could not be retrieved.
    """
    commitments = {
        'Audits': compute_audit_commitment(interval, False),
        'CAPAs': compute_capa_commitment(interval, False), 
        'Complaints': compute_complaint_commitment(interval, False), 
        'Training': compute_training_commitment()[interval]
    }
    min_period = min_period_category = None
    for category, commitment in commitments.items():
        if commitment is not None and (min_period is None or commitment.index[0] > min_period):
            min_period = commitment.index[0]
            min_period_category = category
    no_data_for = sorted(record_type for record_type, data in commitments.items() if data is None)
    if no_data_for:
        return 'Cannot compute commitment because ' + items_in_a_series(no_data_for) + ' data could not be retrieved.'
    commitment = 1
    for cat, wt in COMMITMENT_WTS.items():
        commitment += commitments[cat] * wt
    return commitment, min_period, min_period_category


if __name__ == '__main__':
    st.title('RA/QA KPIs')
    interval = render_interval_filter(PAGE_NAME)
    commitment = compute_commitment(interval)
    show_data_srcs(error_msg=commitment if isinstance(commitment, str) else None)
    if not isinstance(commitment, str):
        commitment, min_period, min_period_category = commitment
        start, end = render_period_filter(PAGE_NAME, interval, default_start=min_period)
        min_period_msg = {
            'Audits': f' as there are no records of audits before that {interval.lower()}',
            'CAPAs': f' as Rad has no records of CAPAs before that {interval.lower()}',
            'Complaints': f' as Rad did not implement the current complaint handling process until partway through the {interval.lower()}',
            'Training': f' as Rad did not implement training in Matrix eQMS until that {interval.lower()}'
        }[min_period_category]
        fig, ax = plot_bar(
            PAGE_NAME,
            commitment,
            interval=interval,
            start=start,
            end=end, 
            bar_kwargs={'color': RAD_COLOR, 'label': '_nolegend_'},
            is_pct=True,
            title='Commitment',
            x_label='Complaint closure ' + interval.lower(),
            y_label='Commitment %',
            min_period_msg=min_period_msg,
            max_period_msg=f' as there may be more audits completed, CAPAs submitted, complaints resolved, and/or QMS training assigned this {interval.lower()}',
            label_missing='Missing data†',
            msgs=['†No audits planned, no CAPAs submitted, no complaints received, and/or no training completed']
        )
        
        # Pie chart of weights
        inset_ax = fig.add_axes([0.1, 0.575, 0.25, 0.25], zorder=3)
        inset_ax.set_title('Weights', fontsize=9, pad=0)
        inset_ax.patch.set_alpha(0.0)
        cmap = create_shifted_cmap('tab10', 4)
        inset_ax.set_xticks([])
        inset_ax.set_yticks([])
        vals = list(COMMITMENT_WTS.values())
        labels = list(COMMITMENT_WTS)
        wedges, texts = inset_ax.pie(
            vals,
            labels=None,
            colors=[cmap(x) for x in range(len(COMMITMENT_WTS))],
            autopct=None,
            wedgeprops={'edgecolor': 'white', 'alpha': 0.6},
        )
        for t in texts:
            t.set_visible(False)
        for i, wedge in enumerate(wedges):
            ang = (wedge.theta2 + wedge.theta1) / 2.0  # angle in degrees
            x = 0.6 * np.cos(np.deg2rad(ang))  # radius scaling -> closer to center
            y = 0.6 * np.sin(np.deg2rad(ang))
            inset_ax.text(
                x, y,
                f'{labels[i]}\n{vals[i]:.0%}',
                ha='center', 
                va='center',
                fontsize=7
            )
        fig.canvas.draw()
        pad = 0.015
        bbox = inset_ax.get_position()
        rect = FancyBboxPatch(
            (bbox.x0 + pad, bbox.y0 + pad),
            bbox.width - pad * 2, 
            bbox.height + pad,
            boxstyle='round,pad=0.01,rounding_size=0.025',
            linewidth=1.2,
            edgecolor='black',
            facecolor=(1, 1, 1, 0.6),  # partially transparent white
            transform=fig.transFigure,  # IMPORTANT: place in figure coords
            zorder=inset_ax.get_zorder() - 1
        )
        fig.add_artist(rect)
        responsive_columns([fig])
