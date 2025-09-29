import json
from typing import Dict, List, Union

from bs4 import BeautifulSoup
import pandas as pd
import requests

from utils.constants import MATRIX_HEADERS, QMS_URL


def get_item_title(item_ref: str) -> str:
    """
    Returns the title of the Matrix QMS project item with the given ID
    
    Parameters:
        item_ref (str): Item ID
        
    Returns:
        str: Item title
        
    Example:
        >>> get_item_title('CAPA-2') -> 'Supplier Control'
    """
    item = requests.get(
        f'{QMS_URL}/item/{item_ref}',
        headers=MATRIX_HEADERS,
    ).json()
    return item['title']


def get_multiselect(category: str) -> List[str]:
    """
    Returns a list of Matrix QMS project fields that are multiselect (dropdowns with max options selected > 1)
    
    Parameters:
        category (str): Matrix item category whose multiselect field names to return
        
    Returns:
        multiselect (List(str)): List of multiselect field names
        
    Example:
        >>> get_multiselect('AUDIT') -> ['Scope', 'Criteria']
    """
    multiselect = []
    cat = requests.get(
        f'{QMS_URL}/cat/{category}',
        headers=MATRIX_HEADERS
    ).json()
    for fld in cat['fieldList']:
        if fld['fieldType'] == 'dropdown':
            param = json.loads(fld['fieldParam'])
            if param['maxItems'] != 1:
                multiselect.append(fld['label'])
    return multiselect


def get_matrix_items(category: str) -> Union[pd.DataFrame, str]:
    """
    Retrieves and processes item data from the Matrix QMS API for a given category.

    This function fetches metadata and item values for all items in the specified category. 
    It builds a structured `DataFrame` with each item's ID, title, and field values. Rich 
    text fields are stripped of HTML tags. Specific field names ("Affects Safety.", "Affects
    Regulatory Conformance.") are disambiguated by appending context (e.g., "(Analysis)" or 
    "(Effectiveness Verification)"). Assumes all items are in the folder "F_<category>-1" (e.g.,
    "F-CAPA-1").

    Parameters:
        category (str): The Matrix QMS category identifier (e.g., 'CAPA').

    Returns:
        Union[pd.DataFrame, str]: A `DataFrame` where each row represents an item in the category, 
            with index ID and columns for Title and all relevant field values, or an error message 
            string if could not connect to Matrix.

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
        # Map field IDs to names
        ids_names = {}
        richtext = []
        for fld in cat['fieldList']:
            id_, name = fld['id'], fld['label']
            if name in ['Affects Safety.', 'Affects Regulatory Conformance.']:
                name = name + ' (Effectiveness Verification)' if name + ' (Analysis)' in ids_names.values() else name + ' (Analysis)'
            ids_names[id_] = name
            if fld['fieldType'] == 'richtext':
                richtext.append(id_)
        # Get all items
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
            item_dict = {'ID': item_ref, 'Title': item['title'], 'Labels': item['labels']}
            for fld_val in item['fieldValList']['fieldVal']:
                item_dict[ids_names[fld_val['id']]] = BeautifulSoup(fld_val['value'], 'html.parser').text if fld_val['id'] in richtext else fld_val['value']
            item_dicts.append(item_dict)
    except Exception as e:
        return f'Could not retrieve data from Matrix:{str(e)}'
    
    return pd.DataFrame.from_records(item_dicts, index='ID')


def map_dropdown_ids(dropdown_keys: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Fetches and maps option IDs to their human-readable labels for specific dropdowns
    in the Matrix QMS project settings.

    This function queries the Matrix QMS API for all project settings, extracts the JSON options
    for each dropdown identified by a key in `dropdown_keys`, and returns a dictionary mapping
    each option's ID to its label.

    Parameters:
        dropdown_keys (list[str]): List of keys identifying the dropdowns in the QMS project settings.

    Returns:
        Dict[str, Dict[str, str]]: A dictionary where each key is a dropdown key, and the value
                                   is another dictionary mapping option IDs (as strings) to their 
                                   labels (as strings).

    Example:
        >>> map_dropdown_ids(['dd_auditTypes'])
        {
            'dd_auditTypes': {'internal': 'Internal', 'external': 'External'}
        }
    """
    dd_ids: Dict[str, Dict[str, str]] = {}
    stgs = requests.get(
        f'{QMS_URL}/setting',
        headers=MATRIX_HEADERS
    ).json()
    for setting in stgs['settingList']:
        if len(dd_ids) == len(dropdown_keys):  # Stop searching if all dropdowns have been found
            break
        if setting['key'] in dropdown_keys:
            dd_options = json.loads(setting['value'])['options']
            dd_ids[setting['key']] = {option['id']: option['label'] for option in dd_options}
    return dd_ids
