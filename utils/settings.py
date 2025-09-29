from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


class PageState:
    """
    Holds state for a single page, including:

    - interval: current interval (value from constants.INTERVALS)
    - periods: dictionary of start/end periods per interval
    - breakdown: selected breakdown category
    - filters: selected filter options per category
    """

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.interval: str = 'Month'
        self.periods: Dict[str, Tuple[Optional[Any], Optional[Any]]] = {}  # interval -> (start, end)
        self.breakdown: Optional[str] = None
        self.filters: Dict[str, List[Any]] = defaultdict(list)  # category -> selected options

    def set_period(self, interval: str, start: Any, end: Any) -> None:
        """Sets the start and end period for a given interval."""
        self.periods[interval] = (start, end)

    def get_period(self, interval: str) -> Tuple[Optional[Any], Optional[Any]]:
        """Gets the start and end period for a given interval. Returns (None, None) if not set."""
        return self.periods.get(interval, (None, None))


class Settings:
    """
    Centralized state container for all pages in the app.

    Attributes:
        pages (Dict[str, PageState]): Dictionary mapping page names to PageState objects.
    """

    def __init__(self) -> None:
        self.pages: Dict[str, PageState] = {}

    def get_page(self, name: str) -> PageState:
        """
        Retrieves the PageState for a given page.

        If the page does not exist, it is created automatically.

        Parameters:
            name (str): Name of the page.

        Returns:
            PageState: The state object for the specified page.
        """
        if name not in self.pages:
            self.pages[name] = PageState(name)
        return self.pages[name]


@st.cache_resource
def get_settings():
    return Settings()
