import numpy as np
import pandas as pd
from scipy.optimize import minimize
import streamlit as st


def compute_trendline(y_values, pred_before=0, pred_after=0, clip_min=None, clip_max=None):
    """
    Computes a linear trendline for the given data with optional prediction padding and clipping.

    Fits a linear model `y = a * x + b` to non-`NaN` values in `y_values` using constrained optimization,
    where the intercept `b` is constrained to be non-negative (b ≥ 0). Optionally predicts values 
    for periods before and after the input data, and clips predicted values to specified bounds.

    Parameters:
        y_values (array-like): Sequence of numeric values (may contain `NaN`s).
        pred_before (Optional[int]): Number of periods to predict before the input data. Defaults to 0.
        pred_after (Optional[int]): Number of periods to predict after the input data. Defaults to 0.
        clip_min (Optional[float]): Minimum value to clip predictions to. Defaults to None.
        clip_max (Optional[float]): Maximum value to clip predictions to. Defaults to None.

    Returns:
        np.ndarray: Predicted trendline values including any before/after extrapolation and clipping.
    """
    period_nos = np.arange(len(y_values))
    mask = ~pd.isna(y_values)
    x, y = period_nos[mask], y_values[mask]
    
    def loss(params):
        a, b = params
        y_pred = a * x + b
        return np.mean((y - y_pred) ** 2)

    constraints = [{'type': 'ineq', 'fun': lambda params: params[1]}]  # b ≥ 0
    res = minimize(loss, x0=[1.0, 0.0], constraints=constraints)

    a, b = res.x
    to_pred = np.concatenate([np.arange(-pred_before, 0), period_nos, np.arange(len(period_nos), len(period_nos) + pred_after)])  # Predict for all periods
    y_pred = a * to_pred + b
    
    if clip_min is not None or clip_max is not None:
        y_pred = np.clip(y_pred, clip_min, clip_max)
        
    return y_pred
