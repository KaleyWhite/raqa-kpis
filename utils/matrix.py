import json

from bs4 import BeautifulSoup
import pandas as pd
import requests
import streamlit as st


# Constants

MATRIX_HEADERS = {
    'authorization': 'Token ' + st.secrets['MATRIX_TOKEN'], 
    #'Content-Type': 'application/json',
    'accept': 'application/json'
}
MATRIX_URL = 'https://radformation.matrixreq.com'
QMS_URL = MATRIX_URL + '/rest/1/QMS'


# Functions

def get_matrix_items(category):
    """
    Retrieves and processes item data from the Matrix QMS API for a given category.

    This function fetches metadata and item values for all items in the specified category 
    from the Matrix QMS system. It builds a structured `DataFrame` with each item's ID, title, 
    and field values. Rich text fields are stripped of HTML tags. Specific field names 
    ("Affects Safety.", "Affects Regulatory Conformance.") are disambiguated by appending 
    context (e.g., "(Analysis)" or "(Effectiveness Verification)").

    Parameters:
        category (str): The Matrix QMS category identifier (e.g., 'CAPA').

    Returns:
        Union[pd.DataFrame, str]: A `DataFrame` where each row represents an item in the category, 
            with columns for ID, Title, and all relevant field values, or an error message string if could not connect to Matrix

    Raises:
        Exception: If authentication with the Matrix API fails due to an invalid or missing token.
    """
    item_dicts = []
    cat = requests.get(
        f'{QMS_URL}/cat/{category}',
        headers=MATRIX_HEADERS
    ).json()
    if 'code' in cat and cat['code'] == 'AuthenticationFailed':
        return 'Could not authenticate with Matrix API token. Double-check your token: https://radformation.matrixreq.com/adminConfig/Token.'
    try:
        ids_names = {}
        richtext = []
        for fld in cat['fieldList']:
            id_, name = fld['id'], fld['label']
            if name in ['Affects Safety.', 'Affects Regulatory Conformance.']:
                name = name + ' (Effectiveness Verification)' if name + ' (Analysis)' in ids_names.values() else name + ' (Analysis)'
            ids_names[id_] = name
            if fld['fieldType'] == 'richtext':
                richtext.append(id_)
        folder = requests.get(
            f'{QMS_URL}/item/F-{category}-1',
            headers=MATRIX_HEADERS,
        ).json()
        item_refs = [item['itemRef'] for item in folder['itemList']]
        for item_ref in item_refs:
            item = requests.get(
                f'{QMS_URL}/item/{item_ref}',
                headers=MATRIX_HEADERS,
            ).json()
            item_dict = {'ID': item_ref, 'Title': item['title']}
            for fld_val in item['fieldValList']['fieldVal']:
                item_dict[ids_names[fld_val['id']]] = BeautifulSoup(fld_val['value'], 'html.parser').text if fld_val['id'] in richtext else fld_val['value']
                item_dicts.append(item_dict)
    except Exception as e:
        return 'Could not retrieve data from Matrix.<br>' + str(e)
    
    return pd.DataFrame.from_records(item_dicts)


def map_dropdown_ids(dropdown_key):
    """
    Fetches and maps the IDs to labels for a specific dropdown in the Matrix QMS project settings
    (see https://radformation.matrixreq.com/adminConfig/QMS-projectsettings-dropddowns).

    This function queries the Matrix QMS API for all settings, extracts the JSON options
    for the dropdown identified by `dropdown_key`, and returns a dictionary mapping each
    option's ID to its human-readable label.

    Parameters:
        dropdown_key (str): The key identifying the dropdown in the QMS project settings.

    Returns:
        dict: A dictionary mapping each option's ID (str) to its label (str).
    """
    stgs = requests.get(
        f'{QMS_URL}/setting',
        headers=MATRIX_HEADERS
    ).json()
    dd_options = next(dict['value'] for dict in stgs['settingList'] if dict['key'] == dropdown_key)
    dd_options = json.loads(dd_options)['options']
    return {option['id']: option['label'] for option in dd_options}
