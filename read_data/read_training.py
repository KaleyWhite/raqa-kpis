from typing import Union

import numpy as np
import pandas as pd
import streamlit as st

from read_data.gdrive import read_gsheet
from utils.constants import INTERVALS


@st.cache_data
def read_training_data() -> Union[pd.DataFrame, str]:
    """
    Reads QMS training data from the "For KPIs" Google Sheet and computes training metrics.

    Returns:
        Union[pd.DataFrame, str]:
            - A DataFrame of training data with additional computed columns, or
            - An error message string if the sheet could not be read.

    The returned DataFrame includes:
        - All original columns from the "Training" sheet.
        - "# Open Trainings Overdue": Difference between "# Open Trainings" and "# Open Trainings NOT Overdue".
        - "% Training Complete": Ratio of completed trainings to total trainings, expressed as a percentage.
        - Period-based columns (one for each entry in INTERVALS), created from the "Month" column.
        - Sorted rows by "Month" and "User".
    """
    df_training = read_gsheet(sheet_name='Training')
    if isinstance(df_training, str):
        return df_training

    # Clean numeric values (remove parentheses and cast to int)
    df_training.iloc[:, 2:] = df_training.iloc[:, 2:].map(lambda x: x.split(' (')[0]).astype(int)

    # Add computed columns
    df_training['# Open Trainings Overdue'] = (
        df_training['# Open Trainings'] - df_training['# Open Trainings NOT Overdue']
    )
    df_training['% Training Complete'] = (
        df_training['# Trainings Completed'] /
        (df_training['# Trainings Completed'] + df_training['# Open Trainings']).replace(0, np.nan)
    ) * 100

    # Add period columns for each defined interval
    for interval_ in INTERVALS:
        df_training[interval_] = df_training['Month'].astype(f'period[{interval_[0]}]')

    # Sort for consistency
    df_training.sort_values(['Month', 'User'], inplace=True)

    return df_training
