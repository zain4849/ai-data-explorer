from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import UploadFile
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_numeric_dtype


DetectedColumnType = Literal["Numeric", "Date", "Categorical"]


@dataclass(frozen=True)
class ColumnSummary:
    name: str
    detected_type: DetectedColumnType
    missing_values: int


def _read_all_bytes(upload: UploadFile) -> bytes:
    upload.file.seek(0) # Reset the file pointer to the beginning of the file
    data = upload.file.read() # Read the entire file into memory
    if not isinstance(data, (bytes, bytearray)): # Check if the data is bytes class or bytearray class or not
        raise ValueError("Upload stream did not return bytes.")
    return bytes(data) # Converts data to bytes object, bytes() is a ctor not a function. This is to make sure data isnt bytearray object.


def load_dataframe_from_upload(upload: UploadFile) -> pd.DataFrame:
    filename = upload.filename or ""
    ext = Path(filename).suffix.lower() # Get the file extension, here Path() is used to get the file extension
    raw = _read_all_bytes(upload) # Read the entire file into memory

    # All of these convert to pandas dataframe object.
    if ext == ".csv":
        return pd.read_csv(io.StringIO(raw.decode("utf-8", errors="replace"))) # decode converts the bytes object to a string object, io.String converts string object to a file like object. Now file_like behaves like a file opened in text mode.

    if ext == ".xlsx":
        # Requires openpyxl at runtime.
        return pd.read_excel(io.BytesIO(raw), engine="openpyxl")

    if ext == ".json":
        text_io = io.StringIO(raw.decode("utf-8", errors="replace"))
        try:

            return pd.read_json(text_io)
        except ValueError:
            # Common alternative: newline-delimited JSON (NDJSON).
            # {"name": "Alice", "age": 25}
            # {"name": "Bob", "age": 30}
            # {"name": "Charlie", "age": 40}
            return pd.read_json(io.StringIO(raw.decode("utf-8", errors="replace")), lines=True)

    raise ValueError("Unsupported file type. Please upload a CSV, XLSX, or JSON file.")


def _compute_missing_counts(df: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    for col in df.columns:
        s = df[col]
        if s.dtype == object or str(s.dtype).startswith("string") or str(s.dtype) == "category":
            ss = s.astype("string")
            missing_mask = ss.isna() | ss.str.strip().eq("")
            counts[str(col)] = int(missing_mask.sum())
        else:
            counts[str(col)] = int(s.isna().sum())
    return counts


def _infer_and_cast_object_series(s: pd.Series) -> tuple[pd.Series, DetectedColumnType]:
    # Try numeric first (common for CSV/JSON string columns).
    non_missing = s.astype("string")
    non_missing = non_missing[~(non_missing.isna() | non_missing.str.strip().eq(""))]
    if len(non_missing) > 0:
        numeric = pd.to_numeric(non_missing, errors="coerce")
        numeric_success = float(numeric.notna().mean())
        if numeric_success >= 0.9:
            casted = pd.to_numeric(s, errors="coerce")
            return casted, "Numeric"

        dt = pd.to_datetime(non_missing, errors="coerce", utc=False)
        dt_success = float(dt.notna().mean())
        if dt_success >= 0.8:
            casted = pd.to_datetime(s, errors="coerce", utc=False)
            return casted, "Date"

    return s, "Categorical"


def normalize_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
    # Make a shallow copy so we can cast columns without mutating caller state.
    df2 = df.copy()
    for col in df2.columns:
        s = df2[col]
        if is_datetime64_any_dtype(s):
            continue
        if is_numeric_dtype(s):
            continue
        if is_bool_dtype(s):
            continue
        if s.dtype == object or str(s.dtype).startswith("string"):
            casted, _ = _infer_and_cast_object_series(s)
            df2[col] = casted
    return df2


def detect_column_types(df: pd.DataFrame) -> dict[str, DetectedColumnType]:
    detected: dict[str, DetectedColumnType] = {}
    for col in df.columns:
        s = df[col]
        if is_numeric_dtype(s):
            detected[str(col)] = "Numeric"
        elif is_datetime64_any_dtype(s):
            detected[str(col)] = "Date"
        else:
            detected[str(col)] = "Categorical"
    return detected


def build_column_summary(df: pd.DataFrame) -> list[ColumnSummary]:
    missing_counts = _compute_missing_counts(df)
    detected_types = detect_column_types(df)
    summary: list[ColumnSummary] = []
    for col in df.columns:
        name = str(col)
        summary.append(
            ColumnSummary(
                name=name,
                detected_type=detected_types.get(name, "Categorical"),
                missing_values=missing_counts.get(name, 0),
            )
        )
    return summary

