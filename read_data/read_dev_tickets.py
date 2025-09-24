from collections import OrderedDict

from jira import JIRA
import pandas as pd
import streamlit as st

from read_data import add_period_cols, correct_date_dtype


@st.cache_data
def read_dev_ticket_data() -> pd.DataFrame:
    """
    Reads development ticket data from Jira for multiple projects, processes issue history,
    and returns a DataFrame with key ticket metrics.

    Parameters:
        None

    Returns:
        pd.DataFrame:
            A DataFrame of development tickets with columns:
            - ID (str): Jira issue ID
            - Creation Date (datetime): When the issue was created
            - Device (str): Project/device name
            - Done Date (datetime): When the issue was marked "Done"
            - Due Date (datetime): Target completion date
            - Priority (str): Ticket priority (normalized so "Normal" = "Medium")
            - Start Date (datetime): When the issue moved to "In Progress"
            - Status (str): Current status
            - Type (str): Issue type (Bug, CVE, Feature, Tech Debt, etc.)
            - Completion Time (timedelta): Time elapsed from start to done
            - Period-related columns (added by `add_period_cols`)
    """
    def stop_checking_history(issue: dict) -> bool:
        """Helper to determine when to stop traversing issue history."""
        return (
            not pd.isna(issue['Start Date']) and
            (issue['Status'] != 'Done' or not pd.isna(issue['Start Date']))
        )
    
    # Target Jira projects
    PROJECT_KEYS = {key: None for key in ['AC', 'CALC', 'CC', 'CH', 'EZF', 'QC', 'RAM', 'RO']}
    
    issue_dicts = []
    jira = JIRA(
        basic_auth=tuple(st.secrets['jira']['basic_auth']),
        server=st.secrets['jira']['server']
    )
    
    for key in PROJECT_KEYS:
        issues = jira.search_issues(
            f'project={key} AND (type=Bug OR type=CVE OR type=Feature OR type="Feature HLD" OR type="Tech Debt" OR type="Tech debt")',
            maxResults=5000,
            fields=['assignee', 'created', 'duedate', 'issuetype', 'priority', 'project', 'status'],
            properties=['id'],
            expand='changelog'
        )
        
        for issue in issues:
            issue_dict = OrderedDict([
                ('ID', issue.id),
                ('Creation Date', issue.fields.created),
                ('Device', issue.fields.project.name),
                ('Done Date', pd.NaT),
                ('Due Date', issue.fields.duedate),
                ('Priority', 'Medium' if issue.fields.priority.name == 'Normal' else issue.fields.priority.name),
                ('Start Date', pd.NaT),
                ('Status', issue.fields.status.name),
                ('Type',
                    'Feature' if issue.fields.issuetype.name.startswith('Feature')
                    else 'Tech Debt' if issue.fields.issuetype.name.lower() == 'tech debt'
                    else issue.fields.issuetype.name
                ),
            ])
            
            # Parse changelog to extract start/done dates
            if issue_dict['Status'] != 'To Do':
                for history in issue.changelog.histories:
                    if stop_checking_history(issue_dict):
                        break
                    for item in history.items:
                        if stop_checking_history(issue_dict):
                            break
                        if item.field == 'status':
                            if item.toString == 'In Progress':
                                issue_dict['Start Date'] = history.created
                            elif item.toString == 'Done':
                                issue_dict['Done Date'] = history.created
            
            issue_dicts.append(issue_dict)

    # Convert to DataFrame
    issue_df = correct_date_dtype(pd.DataFrame.from_records(issue_dicts, index='ID'))
    add_period_cols(issue_df)
    issue_df['Completion Time'] = issue_df['Done Date'] - issue_df['Start Date']
    
    return issue_df
