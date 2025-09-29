
from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd
import streamlit as st
from typing import List, Union


def construct_gcp_creds(scopes: List[str]) -> service_account.Credentials:
    """
    Constructs Google Cloud Platform credentials using a service account stored in Streamlit secrets.

    Parameters:
        scopes (List[str]): A list of OAuth scopes required for the credentials.

    Returns:
        service_account.Credentials: A credentials object that can be used to authenticate
                                     GCP API calls with the specified scopes.

    Example:
        >>> creds = construct_gcp_creds(['https://www.googleapis.com/auth/drive.readonly'])
    """
    return service_account.Credentials.from_service_account_info(st.secrets['gcp_svc_acct'], scopes=scopes)
        

def read_gsheet(spreadsheet_id: str = '1yKiAn_Szx5gW5aGOa85RAl_eScg0vjkGyvQQfGfllLI', sheet_name: str = 'Training', range: str = 'A1:H') -> Union[pd.DataFrame, str]:
    """
    Returns a `DataFrame` of the table from the specified Google Sheet

    Parameters:
        spreadsheet_id (str): The ID of the Google Sheet (found in the URL). Defaults to the "For KPIs" sheet
        sheet_name (str): Name of the sheet in the Google Sheet. Defaults to "Training".
        range (str): The range of cells to read. Defaults to "A1:H".

    Returns:
        Union[pd.DataFrame, str]: The table on that sheet in DataFrame format, or an error message string
                                  if the GSheet could not be read.
    """
    try:
        creds = construct_gcp_creds(['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets'])
        service = build('sheets', 'v4', credentials=creds)
        sheets = service.spreadsheets()

        result = sheets.values().get(spreadsheetId=spreadsheet_id, range=f'{sheet_name}!{range}').execute()['values']
    except Exception as e:
        return f'Could not read from the Google Sheet: {e}'
    
    return pd.DataFrame(result[1:], columns=result[0])
