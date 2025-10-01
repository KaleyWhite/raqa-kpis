from datetime import date
import json
from typing import Optional

import pandas as pd
import requests
import streamlit as st

from read_data import correct_date_dtype
from utils.constants import RAD_DATE


def read_mp_usage() -> pd.DataFrame:
    """
    Retrieves all 'Series Finished Contouring' events from Mixpanel
    between RAD_DATE and today, returning a DataFrame with
    distinct_id and Usage Date.

    'Usage Date' is parsed from 'Record Time' (format '%Y-%m-%dT%H:%M:%S')
    if present and not NA; otherwise, falls back to 'time' (seconds since epoch).
    
    Returns:
        pd.DataFrame: DataFrame with columns 'Account' and 'Usage Date'.
    """
    params = {
        'from_date': RAD_DATE,
        'to_date': date.today().isoformat(),
        'event': '["Series Finished Contouring"]'
    }

    response = requests.get(
        'https://data.mixpanel.com/api/2.0/export/',
        auth=(st.secrets['mixpanel']['secret'], ''),
        params=params,
        stream=True
    )

    # Generator for parsed events
    def parse_event(line: str) -> dict:
        data = json.loads(line)
        #st.write(data)
        if data.get('event') != 'Series Finished Contouring':
            return
        props = data.get('properties', {})
        if 'Record Time' in props and pd.notna(props['Record Time']):
            usage_date = props['Record Time'].split('T')[0]
        else:
            usage_date = pd.to_datetime(props.get('time'), unit='s').strftime('%Y-%m-%d')
        return {'distinct_id': props.get('distinct_id'), 'Usage Date': usage_date}

    events_gen = (
        evt for evt in (parse_event(line) for line in response.iter_lines() if line)
        if evt is not None
    )

    df = pd.DataFrame(events_gen)
    users_df = read_mp_users()
    df = df.join(users_df.set_index('distinct_id')['Account'], on='distinct_id', how='left')
    df['Account'] = df['Account'].fillna('Unknown')
    df.loc[df['distinct_id'].isna(), 'Account'] = 'Unknown'
    df = correct_date_dtype(df)
    df = df[~df['Account'].isin(['Limbus AI', 'Radformation'])]
    df['Device'] = 'Limbus Contour'
    df = df.drop(columns=['distinct_id'])
    
    return df


def read_mp_users() -> pd.DataFrame:
    """
    Retrieves all Mixpanel users (distinct_id) and their 'Center' property.

    Returns:
        pd.DataFrame: DataFrame with columns 'distinct_id' and 'Account'.
    """
    url = 'https://mixpanel.com/api/2.0/engage/'
    results = []
    params = {'limit': 1000}  # max 1000 per request
    next_page: Optional[str] = None

    while True:
        if next_page:
            params['session_id'] = next_page  # pagination token
        response = requests.get(url, auth=(st.secrets['mixpanel']['secret'], ''), params=params)
        response.raise_for_status()
        data = response.json()
        results.extend(data.get('results', []))
        next_page = data.get('next')
        if not next_page:
            break

    # Build DataFrame
    df_users = pd.DataFrame([{
        'distinct_id': user.get('$distinct_id'),
        'Account': user['$properties'].get('Center')
    } for user in results])

    return df_users
