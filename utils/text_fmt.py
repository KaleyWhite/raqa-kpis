import pandas as pd


def items_in_a_series(list, conjunction='and', comma_for_clarity=False):
    """
    Formats list elements as items in a series

    Parameters:
        list (List[str]): Items in the series
        conjunction (Optional[str]): Conjunction ("and" or "or") with which to join the items
        comma_for_clarity (Optional[str]): If `True`, use a comma before the conjunction even if there are only two items in the list
        
    Examples:
        >>> l = items_in_a_series(['a'])
        >>> print(l)
        >>> "a"
        
        >>> l = items_in_a_series(['a', 'b'], 'or')
        >>> print(l)
        >>> "a or b"
        
        >>> l = items_in_a_series(['a', 'b', 'c'])
        >>> print(l)
        >>> "a, b, and c"
    """
    if len(list) == 1:
        return list[0]
    if len(list) == 2:
        return list[0] + (', ' if comma_for_clarity else ' ') + conjunction + ' ' + list[1]
    return ', '.join(list[:-1]) + ', ' + conjunction + ' ' + list[-1]


def period_str(period, interval='Month'):
    """
    Formats a `pd.Timestamp` or `pd.Period` object as a string in the format "<month abbreviation> <4-digit year>" or "Q<quarter number> <4-digit year>", depending on the Streamlit session variable `interval`

    Parameters:
        period (Union[pd.Timestamp, pd.Period]): `Timestamp` or `Period` to format as a string
        interval (str): 'Month' or 'Quarter'. Defaults to 'Month'

    Returns:
        str: String version of the period
    """
    if isinstance(period, pd.Period):
        period = period.to_timestamp()
    if interval == 'Month':
        return period.strftime('%b %Y')
    return f'Q{((period.month - 1) // 3) + 1} {period.year}'
