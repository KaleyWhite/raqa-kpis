from typing import Union

import pandas as pd
import streamlit as st

from read_data import add_period_cols, correct_date_dtype
from read_data.salesforce import get_sf_records, sf


@st.cache_data
def read_usage_data() -> Union[pd.DataFrame, str]:
    """
    Reads product usage data from Salesforce and enriches it with account and device information.

    Parameters:
        None

    Returns:
        Union[pd.DataFrame, str]:
            - A DataFrame containing product usage statistics with columns:
                - Number Of Runs (int)
                - Usage Date (datetime)
                - Account (str)
                - Device (str)
                - Period columns for each interval in INTERVALS
            - A string error message if Salesforce data could not be retrieved.
    """
    if sf is None:
        return 'Could not retrieve usage data from Salesforce.'

    # Get Website Institution data
    webinst_df = get_sf_records('WebsiteInstitution__c', ['Id', 'Name']).set_index('Id')

    # Get Website Institution Product data
    webinstprod_df = get_sf_records(
        'WebsiteInstitutionProduct__c',
        ['Id', 'WebsiteInstitution__c', 'WebInstitution_Product__c']
    ).set_index('Id')

    # Get Usage statistics
    df_usage = get_sf_records(
        'WebsiteProductLicenseDailyStatistic__c',
        ['WebsiteInstitutionProduct__c', 'NumberOfRuns__c', 'Usage_Date__c']
    )
    df_usage = correct_date_dtype(df_usage, ['Usage Date'])

    # Join data to get Account names
    webinstprod_df = webinstprod_df.join(webinst_df, how='left', on='Website Institution').rename(columns={'Name': 'Account'})
    df_usage = df_usage.join(
        webinstprod_df,
        how='left',
        on='Website Institution Product'
    )[['Number Of Runs', 'Usage Date', 'Web Institution Product', 'Account']]

    # Extract device name from "Web Institution Product"
    df_usage['Device'] = df_usage['Web Institution Product'].apply(lambda x: x[x.rfind(' - ') + 3:])
    df_usage = df_usage.drop('Web Institution Product', axis=1)

    add_period_cols(df_usage)

    return df_usage
