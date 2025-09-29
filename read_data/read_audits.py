import json
from typing import List, Union

import pandas as pd
import streamlit as st

from read_data import add_period_cols, correct_date_dtype
from read_data.matrix import get_item_title, get_matrix_items, get_multiselect, map_dropdown_ids
from utils.constants import DATE_COLS


@st.cache_data
def create_findings_df(df_audits):
    """
    Constructs a DataFrame of audit finding data
    
    This function returs a DataFrame with the following columns:
    -  'Audit ID': From the 'ID' column of `df_audits`
    -  'Classification': From the 'findingClassification' value in the 'Findings' JSON
                         string column in `df_audits`
    -  'Referenced Standards': IDs and titles of STD, GUI, and LEG items in the 'ref'
                               value in the 'Findings' JSON sreing column of `df_audits`
    -  'Referenced QMS Documents': IDs and titles of other items in the 'ref' value in the 
                                   'Findings' JSON string column of `df_audits`
                                   
    Parameters:
        df_audits (pd.DataFrame): DataFrame of AUDIT info. Must contain columns 'ID' and 'Findings'
                                   
    Returns:
        df (pd.DataFrame): DataFrame with each row representing an audit finding
    """
    dd_map = map_dropdown_ids(['dd_ncFindingClass'])['dd_ncFindingClass']
    mapped_ids = {}
    row_dicts = []
    for id_, row in df_audits.iterrows():
        findings = json.loads(row['Findings'])
        for finding in findings:
            if len(finding) > 0:
                stds, docs = [], []
                for ref in finding['ref'].split(','):
                    if ref not in mapped_ids:
                        mapped_ids[ref] = get_item_title(ref)
                    full_title = ref + ' ' + mapped_ids[ref]
                    if ref.split('-')[0] in ['GUID', 'LEG', 'STD']:
                        stds.append(full_title)
                    else:
                        docs.append(full_title)
                row_dict = {
                    'Audit ID': id_,
                    'Classification': dd_map[finding['findingClassification']],
                    'Referenced Standards': stds,
                    'Referenced QMS Documents': docs
                }
                row_dicts.append(row_dict)
    df = pd.DataFrame.from_records(row_dicts)
    df['Audit ID'] = df['Audit ID'].astype(str)
    return df


@st.cache_data
def read_audit_data() -> Union[pd.DataFrame, str]:
    """
    Returns a DataFrame of audit data from Matrix.

    The function retrieves audit items from the Matrix QMS project; converts date columns to datetime;
    maps dropdown IDs to human-readable labels; fills missing values; and adds period columns for month, 
    quarter, and year.

    Returns:
        Union[pd.DataFrame, str]: Audit data as a DataFrame, or an error message string if 
                                  the data could not be read from Matrix.
    """ 
    def map_dd(dd_id, col_name, val):
        """Returns the human-readable labels corresponding to the dropdown ID values"""
        if col_name in multiselect_dds:
            return [mapped_dd_ids[dd_id][val_] for val_ in val.split(',')] if isinstance(val, str) else []
        return 'Unknown' if pd.isna(val) else mapped_dd_ids[dd_id][val]
    
    def split_and_clean(x) -> List[str]:
        """
        Normalizes a value into a cleaned list of non-empty strings.

        Handles three cases:
        1. If `x` is already a list, returns a list of non-empty, stripped strings.
        2. If `x` is None or NaN, returns an empty list.
        3. Otherwise, treats `x` as a comma-separated string, splits it, strips whitespace,
        and returns a list of non-empty strings.

        Parameters:
            x (Any): Input value to normalize. Can be a list of strings, a string, or None/NaN.

        Returns:
            List[str]: A list of cleaned, non-empty strings.
        """
        # Already a list → return as-is
        if isinstance(x, list):
            return [item.strip() for item in x if isinstance(item, str) and item.strip()]

        # Null-like → empty list
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return []

        # Otherwise assume string, split on commas
        return [item.strip() for item in str(x).split(',') if item.strip()]
         
    matrix_items = get_matrix_items('AUDIT')
    if isinstance(matrix_items, str):
        return matrix_items

    df_audits = correct_date_dtype(matrix_items, date_format='%Y/%m/%d')
    df_audits['Duration'] = df_audits['Duration'].astype(float)
    multiselect_dds = get_multiselect('AUDIT')  # Fields that allow multiple selections

    dd_ids = {
        'dd_auditTypes': 'Internal/External',
    }
    mapped_dd_ids = map_dropdown_ids(list(dd_ids))
    for dd_id, col in dd_ids.items():  # Replace option ID with its human-readable label
        df_audits[col] = df_audits[col].apply(lambda val: map_dd(dd_id, col, val))

    add_period_cols(df_audits, DATE_COLS['Audits'])
    
    findings_df = create_findings_df(df_audits)
    
    df_audits.index = df_audits.index.astype(str)
    df_audits = df_audits.drop(columns=['Findings'])
    
    # Merge to get lists of finding classifications, findings' referenced standards, and findings' referenced QMS documents
    agg_findings = (
        findings_df
        .assign(
            **{
                'Referenced Standards': findings_df['Referenced Standards'].map(split_and_clean),
                'Referenced QMS Documents': findings_df['Referenced QMS Documents'].map(split_and_clean)
            }
        )
        .groupby('Audit ID')
        .agg({
            'Classification': list,
            'Referenced Standards': lambda s: [item for sublist in s for item in sublist],
            'Referenced QMS Documents': lambda s: [item for sublist in s for item in sublist],
        })
    )
    df_audits = df_audits.join(agg_findings, how='left')

    df_audits['# Findings'] = df_audits['Classification'].apply(lambda lst: len(lst) if isinstance(lst, list) else 0)
    for classification in map_dropdown_ids(['dd_ncFindingClass'])['dd_ncFindingClass']:
        df_audits[f'# {classification}'] = df_audits['Classification'].apply(lambda lst: lst.count(classification) if isinstance(lst, list) else 0)
    
    return df_audits, findings_df
