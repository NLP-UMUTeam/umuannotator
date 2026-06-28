from __future__ import annotations

import sys

import pandas as pd

from umuannotator.document import Corpus
from umuannotator.io.dataframe import dataframe_to_corpus


def read_csv_input(
    input_path: str,
    *,
    text_column: str = "text",
    sep: str = ",",
) -> Corpus:
    source = sys.stdin if input_path == "-" else input_path

    df = pd.read_csv(source, sep=sep)

    return dataframe_to_corpus(
        df,
        text_column=text_column,
    )