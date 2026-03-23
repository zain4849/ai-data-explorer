"""Descriptive statistics: distributions, summary stats, null analysis, outlier detection."""

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd


@dataclass
class ColumnStats:
    name: str
    dtype: str
    count: int
    null_count: int
    null_pct: float
    unique_count: int

    # Numeric stats (None for non-numeric)
    mean: float | None = None
    std: float | None = None
    min: float | None = None
    q25: float | None = None
    median: float | None = None
    q75: float | None = None
    max: float | None = None
    skewness: float | None = None
    kurtosis: float | None = None
    outlier_count: int | None = None

    # Categorical stats
    top_values: list[dict] | None = None

    # Distribution histogram (for numeric)
    histogram: dict | None = None


@dataclass
class DatasetStats:
    row_count: int
    column_count: int
    total_nulls: int
    total_null_pct: float
    memory_usage_bytes: int
    columns: list[ColumnStats] = field(default_factory=list)

    def to_dict(self) -> dict:
        result = {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "total_nulls": self.total_nulls,
            "total_null_pct": round(self.total_null_pct, 2),
            "memory_usage_bytes": self.memory_usage_bytes,
            "columns": [asdict(c) for c in self.columns],
        }
        return result


def compute_descriptive_stats(df: pd.DataFrame) -> DatasetStats:
    """Compute comprehensive descriptive statistics for a DataFrame."""
    total_cells = df.shape[0] * df.shape[1]
    total_nulls = int(df.isnull().sum().sum())

    stats = DatasetStats(
        row_count=len(df),
        column_count=len(df.columns),
        total_nulls=total_nulls,
        total_null_pct=(total_nulls / total_cells * 100) if total_cells > 0 else 0,
        memory_usage_bytes=int(df.memory_usage(deep=True).sum()),
    )

    for col_name in df.columns:
        series = df[col_name]
        col_stat = ColumnStats(
            name=str(col_name),
            dtype=str(series.dtype),
            count=int(series.count()),
            null_count=int(series.isnull().sum()),
            null_pct=round(series.isnull().mean() * 100, 2),
            unique_count=int(series.nunique()),
        )

        if np.issubdtype(series.dtype, np.number):
            _compute_numeric_stats(series, col_stat)
        else:
            _compute_categorical_stats(series, col_stat)

        stats.columns.append(col_stat)

    return stats


def _compute_numeric_stats(series: pd.Series, col: ColumnStats):
    values = series.dropna()
    if len(values) == 0:
        return

    col.mean = _safe_float(values.mean())
    col.std = _safe_float(values.std())
    col.min = _safe_float(values.min())
    col.q25 = _safe_float(values.quantile(0.25))
    col.median = _safe_float(values.median())
    col.q75 = _safe_float(values.quantile(0.75))
    col.max = _safe_float(values.max())

    try:
        col.skewness = _safe_float(values.skew())
    except Exception:
        pass
    try:
        col.kurtosis = _safe_float(values.kurtosis())
    except Exception:
        pass

    # Outlier detection via IQR
    q1, q3 = values.quantile(0.25), values.quantile(0.75)
    iqr = q3 - q1
    if iqr > 0:
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        col.outlier_count = int(((values < lower) | (values > upper)).sum())
    else:
        col.outlier_count = 0

    # Histogram (10 bins)
    try:
        counts, bin_edges = np.histogram(values, bins=min(10, len(values)))
        col.histogram = {
            "counts": counts.tolist(),
            "bin_edges": [round(float(b), 4) for b in bin_edges],
        }
    except Exception:
        pass


def _compute_categorical_stats(series: pd.Series, col: ColumnStats):
    values = series.dropna()
    if len(values) == 0:
        return

    value_counts = values.value_counts().head(10)
    col.top_values = [
        {"value": str(val), "count": int(cnt), "pct": round(cnt / len(values) * 100, 2)}
        for val, cnt in value_counts.items()
    ]


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        if np.isfinite(f):
            return round(f, 6)
        return None
    except (ValueError, TypeError):
        return None
