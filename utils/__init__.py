from collections import OrderedDict
from datetime import datetime
import random

from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import pandas as pd

import streamlit as st

pd.set_option('future.no_silent_downcasting', True)


# Constants

# For each page, the DataFrame columns that should be date data type
DATE_COLS = {
    'AE': {
        'Date Received': 'Received'
    },
    'CAPA': {
        'Date Created': 'Opened', 
        'Due Date': 'Due', 
        'Date of Submission': 'Submitted', 
        'Date of Final Approval': 'Approved'
    },
    'Complaint': {
        'Complaint Created Date': 'Opened', 
        'Complaint Received Date': 'Received', 
        'Investigation Completed Date': 'Investigation Completed',
        'Completed Date': 'Closed'
    }
}
# Approximate logo color for each Rad product
PROD_COLORS = {
    'AutoContour': '#f2b740',
    'ClearCalc': '#4286f4',
    'ClearCheck': '#184664',
    'ChartCheck': '#1f8a4c',
    'EZFluence': '#960052',
    'Limbus Contour': '#33314D',
    'QuickCode': '#27ad60',
    'RadMachine': '#12502c',
    'RadMachine-Diagnostic': '#12502c',
    'RadMonteCarlo': '#0099e1',
    'RadOrthanc': '#2a82bd',
    'N/A': '#a0a0a0'  # E.g., website-related
}
# Data source descriptions to display in expander on each page
SRCS = OrderedDict([
    (
        'AEs',
        (
            'FDA Medical Device Reporting (MDR) <a href="https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmdr/search.CFM">database</a>',
            'The FDA Medical Device Reporting (MDR) <a href="https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmdr/search.CFM">database</a> <a href="https://open.fda.gov/apis/device/event">API</a> is queried for adverse events involving products with manufacturer <em>Radformation</em>.'
        )
    ),
    (
        'Audits',
        (
            '"For KPIs" <a href="https://docs.google.com/spreadsheets/d/1yKiAn_Szx5gW5aGOa85RAl_eScg0vjkGyvQQfGfllLI">Google Sheet</a>',
            'The Google Sheets <a href="https://developers.google.com/workspace/sheets/api/reference/rest">API</a> is used to query the "Audits" <a href="https://docs.google.com/spreadsheets/d/1yKiAn_Szx5gW5aGOa85RAl_eScg0vjkGyvQQfGfllLI/edit?gid=1971664278#gid=1971664278">sheet</a> of the "For KPIs" <a href="https://docs.google.com/spreadsheets/d/1yKiAn_Szx5gW5aGOa85RAl_eScg0vjkGyvQQfGfllLI">Google Sheet</a>.'
        )
    ),
    (
        'CAPAs',
        (
            'Matrix QMS project <a href="https://radformation.matrixreq.com/adminConfig/QMS-projectsettings">settings</a> and <a href="https://radformation.matrixreq.com/adminConfig/QMS-CAPA">CAPA</a> <a href="https://radformation.matrixreq.com/QMS/F-CAPA-1">items</a>',
            'The Matrix <a href="https://app.swaggerhub.com/apis/matrixreq/MatrixALM_QMS/2.5">API</a> is queried for <a href="https://radformation.matrixreq.com/adminConfig/QMS-CAPA">CAPA</a> <a href="https://radformation.matrixreq.com/QMS/F-CAPA-1">items</a> and project <a href="https://radformation.matrixreq.com/adminConfig/QMS-projectsettings">settings</a>'
        )
    ),
    (
        'Complaints',
        (
            '<a href="https://radformation.lightning.force.com/lightning/o/Complaint__c/list">Complaint</a> records in <a href="https://radformation.my.salesforce.com">Salesforce</a>',
            'The Python <code>simple_salesforce</code> <a href="https://pypi.org/project/simple-salesforce">library</a> is used to issue <a href="https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm">SOQL</a> queries against the <a href="https://radformation.my.salesforce.com">Salesforce</a> REST <a href="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest.htm">API</a> to retrieve <a href="https://radformation.lightning.force.com/lightning/o/Complaint__c/list">Complaint</a> information.'
        )
    ),
    (
        'Training',
        (
            '"For KPIs" <a href="https://docs.google.com/spreadsheets/d/1yKiAn_Szx5gW5aGOa85RAl_eScg0vjkGyvQQfGfllLI">Google Sheet</a>',
            'The Google Sheets <a href="https://developers.google.com/workspace/sheets/api/reference/rest">API</a> is used to query the "Training" <a href="https://docs.google.com/spreadsheets/d/1yKiAn_Szx5gW5aGOa85RAl_eScg0vjkGyvQQfGfllLI/edit?gid=85059500#gid=85059500">sheet of the "For KPIs" <a href="https://docs.google.com/spreadsheets/d/1yKiAn_Szx5gW5aGOa85RAl_eScg0vjkGyvQQfGfllLI">Google Sheet</a>.'
        )
    ),
    (
        'Usage',
        (
            '<a href="https://radformation.lightning.force.com/lightning/o/WebsiteInstitution__c/list">WebsiteInstitution</a>, <a href="https://radformation.lightning.force.com/lightning/o/WebsiteInstitutionProduct__c/list">WebsiteInstitutionProduct</a>, and <a href="https://radformation.lightning.force.com/lightning/o/WebsiteProductLicenseDailyStatistic__c/list">WebsiteProductLicenseDailyStatistic</a> records in <a href="https://radformation.my.salesforce.com">Salesforce</a>',
            'The Python <code>simple_salesforce</code> <a href="https://pypi.org/project/simple-salesforce">library</a> is used to issue <a href="https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm">SOQL</a> queries against the <a href="https://radformation.my.salesforce.com">Salesforce</a> REST <a href="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest.htm">API</a> to retrieve <a href="https://radformation.lightning.force.com/lightning/o/WebsiteInstitution__c/list">WebsiteInstitution</a>, <a href="https://radformation.lightning.force.com/lightning/o/WebsiteInstitutionProduct__c/list">WebsiteInstitutionProduct</a>, and <a href="https://radformation.lightning.force.com/lightning/o/WebsiteProductLicenseDailyStatistic__c/list">WebsiteProductLicenseDailyStatistic</a> information.'
        )
    )
])
RAD_COLOR = '#3498db'  # Rad logo color
RAD_DATE = '2016-10-26'  # Rad incorporation date
INTERVALS = ['Month', 'Quarter', 'Year']

def compute_all_periods():
    """
    Compute all available reporting periods since Rad incorporation.

    The function generates period ranges for months, quarters, and years,
    starting from the RAD incorporation date (`RAD_DATE`) up to the current date.

    Returns:
        dict[str, pd.PeriodIndex]: A dictionary where keys are values from `INTERVALS`, and values are corresponding PeriodIndex objects covering the
        full range from `RAD_DATE` through today.
    """
    end = datetime.now().strftime('%Y-%m')
    all_periods = {}
    for interval_ in INTERVALS:
        all_periods[interval_] = pd.period_range(start=RAD_DATE, end=end, freq=interval_[0])
    return all_periods
ALL_PERIODS = compute_all_periods()


# Functions

def add_period_cols(df, cols=None):
    """Adds columns for the month, quarter, and year in which the date value lies.

    Parameters:
        df (pd.DataFrame): `DataFrame` to add the columns to
        cols (Optional[List[str]]): Column names to create new columns based on. If not provided, uses all columns whose names include "date".
        
    Example:
        >>> df = pd.DataFrame({'Created Date': ['2023-01-15', '2023-04-20']})
        >>> df['Created Date'] = pd.to_datetime(df['Created Date'])
        >>> add_period_columns(df)
        >>> print(df)
            Created Date  Created Month Created Quarter Created Year
        0     2023-01-15  2023-01       2023Q1          2023
        1     2023-04-20  2023-04       2023Q2          2023
    """
    if cols is None:
        cols = [col for col in df.columns if 'Date' in col]
    for interval_ in INTERVALS:
        for col in cols:
            df[col.replace('Date', interval_)] = df[col].dt.to_period(interval_[0])


def correct_date_dtype(df, date_columns=None):
    """Convert the given `DataFrame` columns to `pd.datetime` type.

    Parameters:
        df (pd.DataFrame): _DataFrame whose column types to convert
        date_columns (Optional[List[str]]): Columns whose types to convert. Defaults to None. If None, converts all columns whose names contain "Date".

    Returns:
        df: The modified `DataFrame`
    """
    if date_columns is None:
        date_columns = [col for col in df.columns if 'Date' in col]
    df[date_columns] = df[date_columns].apply(pd.to_datetime, errors='coerce').apply(lambda col: col.dt.tz_localize(None))
    return df


def create_shifted_cmap(cmap_name, shift=None):
    """Returns a new `ListedColormap` based on a shifted version of a named colormap.

    This function takes a named Matplotlib colormap (e.g., 'tab10') and rotates its list of colors 
    by the specified amount. If `shift` is not provided, a random shift is applied.

    Parameters:
        cmap_name (str): The name of a discrete colormap available in Matplotlib.
        shift (Optional[int]): The number of colors to rotate the colormap by. 
                               If None, a random shift between 1 and (N-1) is used, 
                               where N is the number of colors in the colormap.

    Returns:
        matplotlib.colors.ListedColormap: A new colormap with colors rotated from the original.

    Example:
        >>> shifted_cmap = create_shifted_cmap('tab10', shift=3)
        >>> plt.bar(range(10), [1] * 10, color=[shifted_cmap(i) for i in range(10)])
    """
    cmap = plt.get_cmap(cmap_name)
    colors = cmap.colors
    if shift is None:
        shift = random.randint(1, len(colors) - 1)
    shifted_colors = colors[shift:] + colors[:shift]
    return ListedColormap(shifted_colors)


def init_page(pg_title):
    """
    Initializes the Streamlit page configuration safely.

    Ensures that `st.set_page_config` is called only once per page
    and always before any other Streamlit commands. This avoids the
    `StreamlitSetPageConfigMustBeFirstCommandError` that occurs when
    multiple imports or reruns cause duplicate calls.

    - Sets the page title to `pg_title` and layout to 'wide'.
    - Uses `st.session_state['page_configured']` as a flag to 
        prevent multiple calls within the same page.

    Returns:
        None
    """
    if 'page_configured' not in st.session_state:
        try:
            st.set_page_config(page_title=pg_title, layout='wide')
            st.session_state['page_configured'] = True
        except Exception as e:
            st.write(str(e))


def show_data_srcs(pg_title='RA/QA KPIs', error_msg=None):
    """
    Displays a collapsible "Data Sources" expander on the Streamlit page.

    The expander shows the data source(s) relevant to the given page.  
    If an error message is provided, the expander defaults to expanded, 
    uses a red ❌ icon instead of ℹ️, and displays the error message in bold red text.

    Parameters:
        pg_title (str, optional): 
            The title of the page whose data sources should be displayed. 
            Defaults to 'RA/QA KPIs'. Uses a global `SRCS` mapping to 
            resolve page-specific data source information.
        error_msg (str, optional): 
            If provided, overrides the default ℹ️ icon with ❌, expands 
            the expander by default, and appends the error message in 
            highlighted red text below the data sources. Defaults to None.

    Returns:
        None
    """
    icon = '❌' if error_msg else 'ℹ️'
    with st.expander(icon + ' Data Sources', expanded=bool(error_msg)):
        if pg_title == 'RA/QA KPIs':
            html = '<br>'.join(f'<strong>{pg}:</strong> {src[0]}' for pg, src in SRCS.items())
        else:
            html = SRCS[pg_title][1]
        if error_msg:
            html += f'<br><br><span style="color:red;font-weight:bold;">{error_msg}</span>' 
        st.html(html)
        