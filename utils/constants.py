from collections import OrderedDict
from datetime import datetime

import pandas as pd
import streamlit as st


# For each page, the DataFrame columns that should be date data type
# DataFrame column : short, human-friendly column name
DATE_COLS = {
    'Adverse Events': {
        'Date of Event': 'Occurred',
        'Date Received': 'Received'
    },
    'Audits': {
        'Planned Start Date': 'Planned Start Date',
        'Start Date': 'Start Date',
        'End Date': 'End Date'
    },
    'CAPAs': {
        'Date Created': 'Opened', 
        'Due Date': 'Due', 
        'Date of Submission': 'Submitted', 
        'Date of Final Approval': 'Approved'
    },
    'Complaints': {
        'Complaint Created Date': 'Opened', 
        'Complaint Received Date': 'Received', 
        'Investigation Completed Date': 'Investigation Completed',
        'Completed Date': 'Closed'
    },
    'Development Tickets': {
        'Creation Date': 'Created',
        'Done Date': 'Done',
        'Due Date': 'Due',
        'Start Date': 'Started'
    },
    'Model Benchmarks': {},
    'Training': {},
    'Usage': {
        'Usage Date': 'Date'
    }
}
# Options for fixed vs. breakdown columns on each page
# If any columns are lists, the breakdown is "value CONTAINS..."
BREAKDOWN_COLS = {
    'Adverse Events': ['Manufacturer', 'Device', 'Device Type', 'Event Type'],
    'Audits': ['Internal/External', 'Referenced Clauses'],
    'Benchmarks': [],
    'CAPAs': ['Disposition', 'Effectiveness Verification Status', 'Priority', 'Problem Type', 'Product', 'Type'],
    'Complaints': ['Device', 'Complaint Status', 'Is Device Malfunction', 'Is Specification Failure', 'Is User Error', 'Is Patient Treated', 'Is Investigation Required', 'Is Safety Issue', 'Is Device Malfunction Cause Injury'],
    'Development Tickets': ['Device', 'Priority', 'Type'],
    'Model Benchmarks': ['Modality', 'Structure', 'Size', 'Pass/Fail'],
    'Training': [],
    'Usage': ['Device']
}

# Data source descriptions to display in expander on each page
SRCS = OrderedDict([
    (
        'Adverse Events',
        (
            'FDA Medical Device Reporting (MDR) <a href="https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmdr/search.CFM">database</a>',
            'The FDA Medical Device Reporting (MDR) <a href="https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmdr/search.CFM">database</a> <a href="https://open.fda.gov/apis/device/event">API</a> is queried for adverse events involving products with manufacturer <em>Radformation</em>.'
        )
    ),
    (
        'Audits',
        (
            'Matrix QMS project <a href="https://radformation.matrixreq.com/adminConfig/QMS-projectsettings">settings</a> and <a href="https://radformation.matrixreq.com/adminConfig/QMS-AUDIT">AUDIT</a> <a href="https://radformation.matrixreq.com/QMS/F-AUDIT-1">items</a>',
            'The Matrix <a href="https://app.swaggerhub.com/apis/matrixreq/MatrixALM_QMS/2.5">API</a> is queried for <a href="https://radformation.matrixreq.com/adminConfig/QMS-AUDIT">AUDIT</a> <a href="https://radformation.matrixreq.com/QMS/F-AUDIT-1">items</a> and project <a href="https://radformation.matrixreq.com/adminConfig/QMS-projectsettings">settings</a>'
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
        'Development Tickets',
        (
            '<a href="https://radformation.atlassian.net/jira">Jira</a> <a href="https://radformation.atlassian.net/issues/?filter=11344">tickets</a>',
            'The Python <code>jira</code> <a href="https://pypi.org/project/jira/">library</a> is used to query the <a href="https://radformation.atlassian.net/jira">Jira</a> <a href="https://developer.atlassian.com/cloud/jira/platform/rest/v2/intro/#about">REST API</a> for <a href="https://radformation.atlassian.net/issues/?filter=11344">ticket</a> data.'
        )
    ),
    (
        'Model Benchmarks',
        (
            '"For KPIs" <a href="https://docs.google.com/spreadsheets/d/1yKiAn_Szx5gW5aGOa85RAl_eScg0vjkGyvQQfGfllLI">Google Sheet</a>',
            'The Google Sheets <a href="https://developers.google.com/workspace/sheets/api/reference/rest">API</a> is used to query the "Model Benchmarks" sheets of the "For KPIs" <a href="https://docs.google.com/spreadsheets/d/1yKiAn_Szx5gW5aGOa85RAl_eScg0vjkGyvQQfGfllLI">Google Sheet</a>.'
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
PROD_ABBRVS = {
    'AutoContour': 'AC',
    'ClearCalc': 'CA',
    'ClearCheck': 'CC',
    'ChartCheck': 'CH',
    'EZFluence': 'EZF',
    'Limbus Contour': 'LC',
    'QuickCode': 'QC',
    'RadMachine': 'RM',
    'RadMachine-Diagnostic': 'RMD',
    'RadMonteCarlo': 'RMC',
    'RadOrthanc': 'RO',
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
RAD_DATE = '2016-10-26'  # Rad incorporation date
INTERVALS = ['Month', 'Quarter', 'Year']


def compute_all_periods():
    """
    Computes all available reporting periods since Rad incorporation.

    The function generates period ranges for months, quarters, and years,
    starting from the incorporation date (`RAD_DATE`) up to the current date.

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

# Matrix

MATRIX_HEADERS = {
    'authorization': 'Token ' + st.secrets['matrix']['token'], 
    'accept': 'application/json'
}
MATRIX_URL = 'https://radformation.matrixreq.com'
QMS_URL = MATRIX_URL + '/rest/1/QMS'

# Mixpanel

JQL_URL = 'https://mixpanel.com/api/2.0/jql'
