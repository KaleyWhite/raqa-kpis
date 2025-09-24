from typing import Union

import pandas as pd
import streamlit as st

from read_data import add_period_cols, correct_date_dtype
from read_data.matrix import get_matrix_items, map_dropdown_ids
from utils.constants import DATE_COLS


@st.cache_data
def read_audit_data() -> Union[pd.DataFrame, str]:
    """
    Returns a DataFrame of audit data from Matrix.

    The function retrieves audit items from the Matrix QMS system, converts date columns to datetime,
    maps dropdown IDs to human-readable labels, fills missing values, and adds period columns for month, 
    quarter, and year.

    Returns:
        Union[pd.DataFrame, str]: Audit data as a DataFrame, or an error message string if 
        the data could not be read from Matrix.
    """
    matrix_items = get_matrix_items('AUDIT')
    if isinstance(matrix_items, str):
        return matrix_items

    df_audits = correct_date_dtype(matrix_items, date_format='%Y/%m/%d')

    dd_ids = {
        'dd_auditingOrganization': 'Auditing Organization',
        'dd_auditType': 'Audit Type',
        'dd_auditTypes': 'Internal/External',
    }
    mapped_dd_ids = map_dropdown_ids(list(dd_ids))
    for dd_id, col in dd_ids.items():
        df_audits[col] = df_audits[col].map(mapped_dd_ids[dd_id])

    df_audits.loc[df_audits['Internal/External'] == 'Internal', 'Auditing Organization'] = 'N/A'
    for col in ['Audit Type', 'Auditing Organization']:
        df_audits[col] = df_audits[col].fillna('Unknown')

    add_period_cols(df_audits, DATE_COLS['Audits'])

    return df_audits
