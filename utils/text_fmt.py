from typing import List, Union

import pandas as pd


def items_in_a_series(items: List[str], conjunction: str = 'and', comma_for_clarity: bool = False) -> str:
    """
    Formats a list of strings as a human-readable series.

    Joins elements with commas and a final conjunction, e.g., "a, b, and c".

    Parameters:
        items (List[str]): Items in the series.
        conjunction (str, optional): Conjunction to use before the last item ("and" or "or"). Defaults to "and".
        comma_for_clarity (bool, optional): If True, use a comma before the conjunction even if there are only two items. Defaults to False.

    Returns:
        str: Formatted string representing the series.

    Examples:
        >>> items_in_a_series(['a'])
        'a'

        >>> items_in_a_series(['a', 'b'], 'or')
        'a or b'

        >>> items_in_a_series(['a', 'b', 'c'])
        'a, b, and c'
    """
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]}{', ' if comma_for_clarity else ' '}{conjunction} {items[1]}"
    return f"{', '.join(items[:-1])}, {conjunction} {items[-1]}"


def period_str(period: Union[pd.Timestamp, pd.Period], interval: str = 'Month') -> str:
    """
    Formats a pandas `Timestamp` or `Period` as a human-readable string.

    Parameters:
        period (Union[pd.Timestamp, pd.Period]): The timestamp or period to format.
        interval (str, optional): Time interval type. Must be one of 'Month', 'Quarter', or 'Year'. Defaults to 'Month'.

    Returns:
        str: Formatted string representing the period.
             - 'Month' -> "Jan 2025"
             - 'Quarter' -> "Q1 2025"
             - 'Year' -> "2025"
    """
    if isinstance(period, pd.Period):
        period = period.to_timestamp()
    
    if interval == 'Month':
        return period.strftime('%b %Y')
    elif interval == 'Quarter':
        quarter = ((period.month - 1) // 3) + 1
        return f'Q{quarter} {period.year}'
    else:  # Year
        return str(period.year)
