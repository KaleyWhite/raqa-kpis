import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import streamlit as st

from read_data.read_benchmarks import read_benchmark_data
from utils import compute_bin_width, init_page, show_data_srcs
from utils.filters import render_breakdown_fixed
from utils.plotting import responsive_columns
from utils.settings import get_settings


if __name__ == '__main__':
    init_page('Model Benchmarks')
PAGE_NAME = os.path.splitext(os.path.basename(__file__))[0]


if __name__ == '__main__':
    st.title(PAGE_NAME)
    df_benchmarks = read_benchmark_data()
    show_data_srcs(PAGE_NAME, df_benchmarks if isinstance(df_benchmarks, str) else None)
    if not isinstance(df_benchmarks, str):
        filtered_df_benchmarks = render_breakdown_fixed(PAGE_NAME, df_benchmarks)
        page = get_settings().get_page(PAGE_NAME)

        hist_cols = ['# Training Data Sets', '# Test Data Sets']
        labels = ['Training', 'Test']
        to_display = []

        breakdown_values = [None] if page.breakdown is None else filtered_df_benchmarks[page.breakdown].unique()

        for val in breakdown_values:
            df_plot = filtered_df_benchmarks if val is None else filtered_df_benchmarks[filtered_df_benchmarks[page.breakdown] == val]
            title = 'Dataset Sizes' if val is None else f'Dataset Sizes: {page.breakdown} = {val}'

            fig, ax = plt.subplots()
            ax.set_title(title)
            ax.set_ylabel('# Datasets')
            ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

            # Compute bin width
            series_list = [df_plot[col] for col in hist_cols]
            bin_width = compute_bin_width(series_list)
            overall_min = min(s.min() for s in series_list)
            overall_max = max(s.max() for s in series_list)
            bins = np.arange(overall_min, overall_max + bin_width, bin_width)

            # Plot each histogram separately so they overlap
            for s, label in zip(series_list, labels):
                ax.hist(s, bins=bins, alpha=0.5, edgecolor='black', label=label)
            ax.set_xlabel('Dataset Size')
            ax.set_ylabel('# Structures')
            ax.legend()
            to_display.append(fig)

        responsive_columns(to_display)
