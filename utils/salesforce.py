import re

import pandas as pd
from simple_salesforce import Salesforce
import streamlit as st


sf = Salesforce(
    username=st.secrets['SF_USER'],
    password=st.secrets['SF_PWD'],
    security_token=st.secrets['SF_TOKEN'],
    instance='radformation.my.salesforce.com'
)
    
    
def get_sf_records(obj, flds=None):
    """
    Retrieves and formats Salesforce records of the given object type.

    This function queries Salesforce for all records of the specified object type (`obj`)
    and returns them as a pandas `DataFrame`. If no fields are specified, all available fields
    are retrieved. Field names are transformed into human-readable labels by:
    - Removing the "__c" suffix
    - Replacing underscores with spaces
    - Splitting camelCase words

    If a field contains a dictionary (e.g., from a related object), its keys are also
    flattened and made human-readable with the parent field name prefixed.

    Parameters:
        obj (str): The name of the Salesforce object to query (e.g., 'Account', 'Case').
        flds (Optional[List[str]]): A list of field names to retrieve. If `None`, all fields are fetched.

    Returns:
        pd.DataFrame: A `DataFrame` containing the queried records with human-readable column names.
    """
    def human_friendly(key):
        no_custom_suffix = re.sub(r'__c$', r'', key)
        no_underscores = re.sub(r'_+', r' ', no_custom_suffix)
        no_camel_case = re.sub(r'([a-z])([A-Z])', r'\g<1> \g<2>', no_underscores)
        return no_camel_case
    if flds is None:
        res = sf.query_all(f'SELECT FIELDS(ALL) FROM {obj} LIMIT 1')
        flds = [k for k in res['records'][0] if k != 'attributes']
    records = []
    for record in sf.query_all_iter(f'SELECT {",".join(flds)} FROM {obj}'):
        record_dict = {}
        for fld in flds:
            val = record[fld]
            human_fld = human_friendly(fld)
            if isinstance(val, dict):
                for k, v in val.items():
                    human_k = human_friendly(k)
                    record_dict[human_fld + ' ' + human_k] = v
            else:
                record_dict[human_fld] = val 
        records.append(record_dict)
    return pd.DataFrame.from_records(records)
