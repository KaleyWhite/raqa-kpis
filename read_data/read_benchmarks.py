from typing import Union

import numpy as np
import pandas as pd
import streamlit as st

from read_data.gdrive import read_gsheet


@st.cache_data   
def read_benchmark_data() -> Union[pd.DataFrame, str]:
    """
    Reads and processes the "Model Benchmarks" Google Sheet data.

    For each sheet in ['Dataset Sizes', 'DSC', 'Sensitivity/Specificity', 'IOV']:
    - Reads the sheet using `read_gsheet`.
    - Drops the 'AC Versions' column and sets ['Modality', 'Structure'] as index.
    - Converts all numeric columns (except 'Size') to numeric types.
    - For the 'DSC' sheet, adds a 'Pass/Fail' column based on 'DSC Mean' vs 'Pass Criteria (DSC Mean)'.
    - For the 'IOV' sheet, computes 'Mean Human IOV' as the mean across columns starting with 'Observer #', then drops those observer columns.
    - Joins all sheets into a single DataFrame.

    Returns:
        Union[pd.DataFrame, str]:  
            - A combined DataFrame with all benchmark sheets if successful.  
            - A descriptive error message (str) if reading or processing fails.
    """
    benchmark_df = None
    idx_cols = ['Modality', 'Structure']
    try:
        for sht_name in ['Dataset Sizes', 'DSC', 'Sensitivity/Specificity', 'IOV']:
            df = read_gsheet(sheet_name='Model Benchmarks - ' + sht_name)
            df = df.drop(columns=['AC Versions']).set_index(idx_cols)
            cols_to_convert = df.columns.difference(['Size'])
            df[cols_to_convert] = df[cols_to_convert].apply(pd.to_numeric, errors='coerce')

            if sht_name == 'DSC':
                df['Pass/Fail'] = np.where(df['DSC Mean'] >= df['Pass Criteria (DSC Mean)'], 'Pass', 'Fail')
            elif sht_name == 'IOV':
                df['Mean Human IOV'] = df.filter(like='Observer #').mean(axis=1)
                df = df.drop(columns=df.filter(like='Observer #').columns)

            benchmark_df = df if benchmark_df is None else benchmark_df.join(df, how='outer')

        benchmark_df = benchmark_df.reset_index()
        return benchmark_df

    except Exception as e:
        return f'Could not read "Model Benchmarks" table(s) from the "For KPIs" GSheet: {e}'
    