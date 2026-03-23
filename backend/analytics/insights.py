"""Structured insight generation: trends, anomalies, correlations, key drivers, segments."""

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from ..llm import call_llm
from ..logger_config import logger


@dataclass
class Insight:
    type: str  # trend, anomaly, correlation, driver, segment
    title: str
    description: str
    importance: float = 0.5  # 0-1 score


@dataclass
class StructuredInsights:
    trends: list[Insight] = field(default_factory=list)
    anomalies: list[Insight] = field(default_factory=list)
    correlations: list[Insight] = field(default_factory=list)
    key_drivers: list[Insight] = field(default_factory=list)
    segments: list[Insight] = field(default_factory=list)
    narrative: str = ""

    def to_dict(self) -> dict:
        return {
            "trends": [asdict(i) for i in self.trends],
            "anomalies": [asdict(i) for i in self.anomalies],
            "correlations": [asdict(i) for i in self.correlations],
            "key_drivers": [asdict(i) for i in self.key_drivers],
            "segments": [asdict(i) for i in self.segments],
            "narrative": self.narrative,
        }


def generate_structured_insights(df: pd.DataFrame) -> StructuredInsights:
    """Generate structured insights from a DataFrame using statistical analysis + LLM."""
    insights = StructuredInsights()

    if df.empty or len(df) < 2:
        insights.narrative = "Not enough data for insight generation."
        return insights

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime", "datetime64"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # --- Trends (time-series direction) ---
    if datetime_cols and numeric_cols:
        insights.trends = _detect_trends(df, datetime_cols[0], numeric_cols)

    # --- Anomalies (outliers via IQR) ---
    if numeric_cols:
        insights.anomalies = _detect_anomalies(df, numeric_cols)

    # --- Correlations ---
    if len(numeric_cols) >= 2:
        insights.correlations = _detect_correlations(df, numeric_cols)

    # --- Key drivers ---
    if len(numeric_cols) >= 2:
        insights.key_drivers = _detect_key_drivers(df, numeric_cols)

    # --- Segments ---
    if categorical_cols and numeric_cols:
        insights.segments = _detect_segments(df, categorical_cols, numeric_cols)

    # --- LLM narrative ---
    try:
        preview = df.head(10).to_string()
        stat_summary = _build_stat_summary(insights)
        prompt = f"""You're a data analyst. Given the data below and the statistical findings,
write a concise narrative (3-5 sentences) explaining the key insights.

Data preview:
{preview}

Statistical findings:
{stat_summary}

Keep the answer concise and actionable.
"""
        insights.narrative = call_llm(prompt)
    except Exception as exc:
        logger.warning("Failed to generate narrative: %s", exc)
        insights.narrative = _build_stat_summary(insights)

    return insights


def _detect_trends(df: pd.DataFrame, time_col: str, numeric_cols: list[str]) -> list[Insight]:
    trends = []
    sorted_df = df.sort_values(time_col)
    for col in numeric_cols[:5]:
        values = sorted_df[col].dropna()
        if len(values) < 3:
            continue
        first_half = values.iloc[: len(values) // 2].mean()
        second_half = values.iloc[len(values) // 2 :].mean()
        if first_half == 0:
            continue
        change_pct = ((second_half - first_half) / abs(first_half)) * 100
        if abs(change_pct) > 5:
            direction = "increasing" if change_pct > 0 else "decreasing"
            trends.append(Insight(
                type="trend",
                title=f"{col} is {direction}",
                description=f"{col} changed by {change_pct:.1f}% from the first half to the second half of the dataset.",
                importance=min(abs(change_pct) / 100, 1.0),
            ))
    return trends


def _detect_anomalies(df: pd.DataFrame, numeric_cols: list[str]) -> list[Insight]:
    anomalies = []
    for col in numeric_cols[:5]:
        values = df[col].dropna()
        if len(values) < 4:
            continue
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = values[(values < lower) | (values > upper)]
        if len(outliers) > 0:
            pct = (len(outliers) / len(values)) * 100
            anomalies.append(Insight(
                type="anomaly",
                title=f"Outliers in {col}",
                description=f"{len(outliers)} outlier(s) ({pct:.1f}%) detected in {col} using IQR method. Range: [{lower:.2f}, {upper:.2f}].",
                importance=min(pct / 20, 1.0),
            ))
    return anomalies


def _detect_correlations(df: pd.DataFrame, numeric_cols: list[str]) -> list[Insight]:
    correlations = []
    try:
        corr_matrix = df[numeric_cols].corr()
        seen = set()
        for i, col1 in enumerate(numeric_cols):
            for j, col2 in enumerate(numeric_cols):
                if i >= j:
                    continue
                key = tuple(sorted([col1, col2]))
                if key in seen:
                    continue
                seen.add(key)
                r = corr_matrix.loc[col1, col2]
                if pd.isna(r):
                    continue
                if abs(r) > 0.7:
                    strength = "strong positive" if r > 0 else "strong negative"
                    correlations.append(Insight(
                        type="correlation",
                        title=f"{strength.title()} correlation: {col1} & {col2}",
                        description=f"Pearson correlation coefficient: {r:.3f}",
                        importance=abs(r),
                    ))
    except Exception:
        pass
    return correlations


def _detect_key_drivers(df: pd.DataFrame, numeric_cols: list[str]) -> list[Insight]:
    """Find which columns have the highest variance (potential key drivers)."""
    drivers = []
    try:
        for col in numeric_cols[:5]:
            values = df[col].dropna()
            if len(values) < 2:
                continue
            cv = values.std() / abs(values.mean()) if values.mean() != 0 else 0
            if cv > 0.5:
                drivers.append(Insight(
                    type="driver",
                    title=f"High variability in {col}",
                    description=f"Coefficient of variation: {cv:.2f}. This column shows significant spread and may be a key driver.",
                    importance=min(cv, 1.0),
                ))
    except Exception:
        pass
    return sorted(drivers, key=lambda d: d.importance, reverse=True)[:3]


def _detect_segments(df: pd.DataFrame, cat_cols: list[str], num_cols: list[str]) -> list[Insight]:
    segments = []
    cat_col = cat_cols[0]
    num_col = num_cols[0]
    try:
        groups = df.groupby(cat_col)[num_col].agg(["mean", "count"])
        groups = groups[groups["count"] >= 2].sort_values("mean", ascending=False)
        if len(groups) >= 2:
            top = groups.index[0]
            bottom = groups.index[-1]
            segments.append(Insight(
                type="segment",
                title=f"Segment analysis: {cat_col}",
                description=f"Highest avg {num_col}: '{top}' ({groups.loc[top, 'mean']:.2f}). Lowest: '{bottom}' ({groups.loc[bottom, 'mean']:.2f}).",
                importance=0.7,
            ))
    except Exception:
        pass
    return segments


def _build_stat_summary(insights: StructuredInsights) -> str:
    lines = []
    for section_name, items in [
        ("Trends", insights.trends),
        ("Anomalies", insights.anomalies),
        ("Correlations", insights.correlations),
        ("Key Drivers", insights.key_drivers),
        ("Segments", insights.segments),
    ]:
        if items:
            lines.append(f"\n{section_name}:")
            for item in items:
                lines.append(f"  - {item.title}: {item.description}")
    return "\n".join(lines) if lines else "No significant statistical findings."
