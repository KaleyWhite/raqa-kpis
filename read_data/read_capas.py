from typing import Union

import numpy as np
import pandas as pd
import streamlit as st

from read_data import add_period_cols, correct_date_dtype
from read_data.matrix import get_matrix_items, map_dropdown_ids
from utils.constants import DATE_COLS


@st.cache_data
def read_capa_data() -> Union[pd.DataFrame, str]:
    """
    Reads CAPA data from Matrix, processes date and dropdown fields,
    and returns a cleaned DataFrame.

    Parameters:
        None

    Returns:
        Union[pd.DataFrame, str]:
            - A DataFrame containing processed CAPA data.
            - A string with an error message if the data could not be read.
    """
    def compute_status(row):
        return 'Closed' if any('Closed' in lbl for lbl in row['Labels']) else 'Open'
    
    def compute_age(row):
        end_date = pd.Timestamp.today().normalize() if row['Status'] == 'Open' else row['Date of Submission']
        return (end_date - row['Date Created']).days
    
    matrix_items = get_matrix_items('CAPA')
    if isinstance(matrix_items, str):
        return matrix_items
    
    df_capas = correct_date_dtype(matrix_items, date_format='%Y/%m/%d')
    st.write(df_capas)
    df_capas['Status'] = df_capas.apply(compute_status, axis=1)
    df_capas['Age'] = df_capas.apply(compute_age, axis=1)

    dd_ids = {
        'dd_dispositions': 'Disposition',
        'dd_effectivenessVerificationStatus': 'Effectiveness Verification Status',
        'dd_CAPA_Priority': 'Priority',
        'dd_CAPA_Problem_Types': 'Problem Type',
        'dd_CAPA_Product': 'Product',
        'dd_CA_Types': 'Type'
    }

    mapped_dd_ids = map_dropdown_ids(list(dd_ids))

    # Normalize product names (remove version numbers and UDIs)
    for id in mapped_dd_ids['dd_CAPA_Product']:
        mapped_dd_ids['dd_CAPA_Product'][id] = (
            mapped_dd_ids['dd_CAPA_Product'][id].split(' ')[0]
        )

    # Replace dropdown IDs in DataFrame with labels
    for dd_id, col in dd_ids.items():
        df_capas[col] = df_capas[col].map(mapped_dd_ids[dd_id])

    add_period_cols(df_capas, DATE_COLS['CAPAs'])

    return df_capas
