import re
from typing import Union

import pandas as pd
import requests
import streamlit as st

from read_data import add_period_cols
from utils.constants import RAD_DATE


@st.cache_data
def read_ae_data() -> Union[pd.DataFrame, str]:
    """
    Returns a `DataFrame` of adverse event data for certain device types, from the FDA AE database 
    API.

    The function fetches AE reports from the FDA API, normalizes manufacturer and device names, 
    converts date fields to `datetime`, and adds period columns for month, quarter, and year using 
    `add_period_cols`. Restricts results to those received since Rad was incorporated.

    Returns:
        Union[pd.DataFrame, str]: A `DataFrame` containing adverse event data, or an error string if
                                  the API request failed.
    """
    def normalize_manufacturer_name(name: str) -> str:
        """
        Normalizes "device.manufacturer_d_name" API field.
        -  Removes suffixes like "inc", "gmbh", and "publ".
        -  Corrects certain spellings.
        """
        name = re.sub(r',? INC.?| GMBH| (PUBL)', r'', name).strip()
        if name.upper() in ['', 'UNK', 'UNKNOWN']:
            return 'Unknown'
        if name.startswith('ACCURAY'):
            name = 'ACCURAY'
        elif name.startswith('BRAINLAB') or name.startswith('BRAIN-LAB'):
            name = 'BRAINLAB'
        elif name == 'COMPUTERIZED MEDICAL SYSTEMS':
            name = 'CMS'
        elif 'ELEKTA' in name:
            name = 'ELEKTA'
        elif name.startswith('NUCLETRON'):
            name = 'NUCLETRON'
        elif name.startswith('PHILIPS') or name.startswith('PHILLIPS'):
            name = 'PHILIPS'
        elif name.startswith('RAYSEARCH'):
            name = 'RAYSEARCH'
        elif name.startswith('REFLEXION'):
            name = 'REFLEXION'
        elif name.startswith('SIEMENS'):
            name = 'SIEMENS'
        elif name.startswith('VARIAN'): 
            name = 'VARIAN'
        return name

    def normalize_device_name(name: str) -> str:
        """
        Normalizes "device.brand_name" API field value
        """
        name = re.sub(r'( ?\d+.\d+,? ?)+| TREATMENT PLANNING SYSTEM', r'', name)
        name = re.sub(r'\(SWIFT\)', 'SWIFT', name).strip()
        if not name:
            return 'Unknown'
        if name == 'BRAIN-LAB':
            name = 'BRAINLAB'
        elif name.startswith('CYBERKNIFE'):
            name = 'CYBERKNIFE'
        elif name.startswith('FOCAL'):
            name = 'FOCAL'
        elif name.startswith('IPLAN'):
            name = 'IPLAN'
        elif name.startswith('ONCENTRA MASTERPLAN'):
            name = 'ONCENTRA MASTERPLAN'
        elif 'PINNACLE' in name:
            name = 'PINNACLE'
        elif 'PRECISION' in name:
            name = 'PRECISION'
        elif name.startswith('SYNGO.VIA'):
            name = 'SYNGO.VIA'
        elif name.startswith('XIO'):
            name = 'XIO'
        return name

    device_names = [
        'Radiological Image Processing Software For Radiation Therapy', 
        'System, Planning, Radiation Therapy Treatment'
    ]
    search_query = (
        '(' + ' OR '.join(f'device.openfda.device_name:"{name}"' for name in device_names) +
        ' OR manufacturer_name:"Radformation Inc.")' +
        f' AND date_received:[{RAD_DATE.replace("-", "")} TO *]'
    )

    res = requests.get(
        'https://api.fda.gov/device/event.json',
        params={'search': search_query, 'limit': 1000},
    ).json()

    if 'error' in res:
        if res['error'] != 'NOT_FOUND':
            return res['error']
    else:
        aes = []
        for ae in res['results']:
            aes.append({
                'Manufacturer': normalize_manufacturer_name(ae['device'][0]['manufacturer_d_name']),
                'Device': normalize_device_name(ae['device'][0]['brand_name']),
                'Device Type': ae['device'][0]['openfda']['device_name'],
                'Date of Event': pd.NaT if 'date_of_event' not in ae else pd.to_datetime(ae['date_of_event'], format='%Y%m%d'),
                'Date Received': pd.to_datetime(ae['date_received'], format='%Y%m%d'),
                'Event Type': 'Unknown' if ae['event_type'] == 'No answer provided' else ae['event_type']
            })
        df_aes = pd.DataFrame.from_records(aes)

    add_period_cols(df_aes)
    return df_aes
