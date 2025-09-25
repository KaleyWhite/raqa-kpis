from typing import Union

import pandas as pd
import streamlit as st

from utils.constants import DATE_COLS
from read_data import add_period_cols, correct_date_dtype
from read_data.salesforce import get_sf_records, sf


@st.cache_data
def read_complaint_data() -> Union[pd.DataFrame, str]:
    """
    Reads complaint data from Salesforce, processes dates and fields,
    and returns a cleaned DataFrame.

    Parameters:
        None

    Returns:
        Union[pd.DataFrame, str]:
            - A DataFrame containing processed complaint data.
            - A string with an error message if Salesforce data could not be retrieved.
    """
    if sf is None:
        return 'Could not retrieve complaint data from Salesforce.'

    df_complaints = correct_date_dtype(get_sf_records('Complaint__c'))

    # Normalize field names
    df_complaints = df_complaints.rename(columns={'Device Name': 'Device'})

    # Default missing values
    df_complaints['Is Safety Issue'] = df_complaints['Is Safety Issue'].fillna('No')

    # Derived time durations
    df_complaints['# Days to Open'] = (
        df_complaints['Complaint Created Date'] - df_complaints['Complaint Received Date']
    ).dt.days
    df_complaints['# Days Open'] = (
        df_complaints['Completed Date'] - df_complaints['Complaint Created Date']
    ).dt.days

    add_period_cols(df_complaints, DATE_COLS['Complaints'])

    return df_complaints
