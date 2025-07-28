from googleapiclient.discovery import build
from google.oauth2 import service_account
import numpy as np
import pandas as pd
import requests
import streamlit as st

from utils import DATE_COLS, add_period_cols, correct_date_dtype
from utils.matrix import get_matrix_items
from utils.salesforce import get_sf_records


@st.cache_data
def read_aes():
    """
    Returns a `DataFrame` of Radformation product adverse event data from the FDA adverse event database API

    Returns:
        pd.DataFrame: Adverse event data
    """
    res = requests.get(
        'https://api.fda.gov/device/event.json',
        params={
            'search': 'manufacturer_name:Radformation, Inc.',
        },
    ).json()
    df_aes = pd.DataFrame({
        'Device Name': pd.Series(dtype='str'),
        'Date Received': pd.Series(dtype='datetime64[ns]')
    })
    if 'error' in res:
        if res['error'] != 'NOT_FOUND':
            return res['error']
    else:
        aes = []
        for ae in res['results']:
            if ae['manufacturer_name'] == 'Radformation, Inc.':
                aes.append({'Device Name': ae['device']['brand_name'], 'Date Received': pd.to_datetime(ae['date_received'], 'YMD')})
        df_aes = pd.concat([df_aes, pd.DataFrame.from_records(aes)])

    add_period_cols(df_aes)

    return df_aes

@st.cache_data
def read_audits():
    """
    Returns a `DataFrame` of audit data from the "For KPIs" Google Sheet

    Returns:
        pd.DataFrame: Audit data
    """
    df_audits = read_gsheet('Audits')
    df_audits.iloc[:, 1:] = df_audits.iloc[:, 1:].astype(int).fillna(0)
    
    # Create the transformed DataFrame
    df_internal = df_audits[['Month', '# Planned Internal', '# Completed Internal']].copy()
    df_internal.columns = ['Month', 'Planned', 'Completed']
    df_internal['Type'] = 'Internal'

    df_external = df_audits[['Month', '# Planned External', '# Completed External']].copy()
    df_external.columns = ['Month', 'Planned', 'Completed']
    df_external['Type'] = 'External'

    # Concatenate and reorder columns
    df_audits = pd.concat([df_internal, df_external], ignore_index=True)
    df_audits = df_audits[['Month', 'Type', 'Planned', 'Completed']]
    df_audits['Planned'] = df_audits['Planned'].astype(int)
    df_audits['Completed'] = df_audits['Completed'].astype(int)
        
    for interval_ in ['Month', 'Quarter']:
        df_audits[interval_] = df_audits['Month'].astype('period[' + interval_[0] + ']')
    
    return df_audits


@st.cache_data
def read_capas():
    """
    Returns a `DataFrame` of CAPA data from Matrix

    Returns:
        pd.DataFrame: CAPA data
    """
    df_capas = correct_date_dtype(get_matrix_items('CAPA'))
    add_period_cols(df_capas, DATE_COLS['CAPA'])
    
    return df_capas


@st.cache_data
def read_complaints():
    """
    Returns a `DataFrame` of complaint data from Salesforce

    Returns:
        pd.DataFrame: Complaint data
    """
    df_complaints = correct_date_dtype(get_sf_records('Complaint__c'))
    
    df_complaints['Device Type'].fillna('N/A', inplace=True)

    df_complaints['# Days to Open'] = (df_complaints['Complaint Created Date'] - df_complaints['Complaint Received Date']).dt.days
    df_complaints['# Days Open'] = (df_complaints['Completed Date'] - df_complaints['Complaint Created Date']).dt.days

    add_period_cols(df_complaints, DATE_COLS['Complaint'])
    
    return df_complaints


def read_gsheet(sheet_name):
    """
    Returns a `DataFrame` of a table from the "For KPIs" Google Sheet

    Parameters:
        sheet_name (str): Name of the sheet in the "For KPIs" Google Sheet

    Returns:
        pd.DataFrame: The table on that sheet in `DataFrame` format
    """
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(st.secrets['gcp_svc_acct'], scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)
    sheets = service.spreadsheets()

    result = sheets.values().get(spreadsheetId='1yKiAn_Szx5gW5aGOa85RAl_eScg0vjkGyvQQfGfllLI', range=f'{sheet_name}!A1:H').execute()['values']
    return pd.DataFrame(result[1:], columns=result[0])


@st.cache_data
def read_training():
    """
    Returns a `DataFrame` of QMS training data from the "For KPIs" Google Sheet

    Returns:
        pd.DataFrame: Training data
    """
    df_training = read_gsheet('Training')
    df_training.iloc[:, 2:] = df_training.iloc[:, 2:].map(lambda x: x.split(' (')[0]).astype(int)
    df_training['# Open Trainings Overdue'] = df_training['# Open Trainings'] - df_training['# Open Trainings NOT Overdue']
    df_training['% Training Complete'] = df_training['# Trainings Completed'] / (df_training['# Trainings Completed'] + df_training['# Open Trainings']).replace(0, np.nan) * 100
    df_training['Quarter'] = df_training['Month'].astype('period[Q]')
    df_training['Month'] = df_training['Month'].astype('period[M]')
    df_training.sort_values(['Month', 'User'], inplace=True)
    
    return df_training


@st.cache_data
def read_usage():
    """
    Returns a `DataFrame` of product usage data from Salesforce

    Returns:
        pd.DataFrame: Usage data
    """
    webinst_df = get_sf_records('WebsiteInstitution__c', ['Id', 'Name']).set_index('Id')
    webinstprod_df = get_sf_records('WebsiteInstitutionProduct__c', ['Id', 'WebsiteInstitution__c', 'WebInstitution_Product__c']).set_index('Id')
    df_usage = correct_date_dtype(get_sf_records('WebsiteProductLicenseDailyStatistic__c', ['WebsiteInstitutionProduct__c', 'NumberOfRuns__c', 'Usage_Date__c']), ['Usage Date'])

    webinstprod_df = webinstprod_df.join(webinst_df, how='left', on='Website Institution').rename(columns={'Name': 'Account'})
    df_usage = df_usage.join(webinstprod_df, how='left', on='Website Institution Product')[['Number Of Runs', 'Usage Date', 'Web Institution Product', 'Account']]
    df_usage['Device'] = df_usage['Web Institution Product'].apply(lambda x: x[x.rfind(' - ') + 3:])
    df_usage.drop('Web Institution Product', axis=1, inplace=True)
    
    df_usage['Month'] = df_usage['Usage Date'].dt.to_period('M')
    df_usage['Quarter'] = df_usage['Usage Date'].dt.to_period('Q')
    
    return df_usage
