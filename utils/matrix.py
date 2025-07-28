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
        pd.DataFrame: A `DataFrame` where each row represents an item in the category, 
                      with columns for ID, Title, and all relevant field values.

    Raises:
        Exception: If authentication with the Matrix API fails due to an invalid or missing token.
    """
    qms_url = MATRIX_URL + '/rest/1/QMS'
    item_dicts = []
    cat = requests.get(
        f'{qms_url}/cat/{category}',
        headers=MATRIX_HEADERS
    ).json()
    if cat['code'] == 'AuthenticationFailed':
        raise Exception('Could not authenticate with Matrix API token ' + st.secrets['MATRIX_TOKEN'] + '. Double-check your token: https://radformation.matrixreq.com/adminConfig/Token.')
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
        f'{qms_url}/item/F-{category}-1',
        headers=MATRIX_HEADERS,
    ).json()
    item_refs = [item['itemRef'] for item in folder['itemList']]
    for item_ref in item_refs:
        item = requests.get(
            f'{qms_url}/item/{item_ref}',
            headers=MATRIX_HEADERS,
        ).json()
        item_dict = {'ID': item_ref, 'Title': item['title']}
        for fld_val in item['fieldValList']['fieldVal']:
            item_dict[ids_names[fld_val['id']]] = BeautifulSoup(fld_val['value'], 'html.parser').text if fld_val['id'] in richtext else fld_val['value']
            item_dicts.append(item_dict)
    return pd.DataFrame.from_records(item_dicts)
