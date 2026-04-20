"""
tools/analysis.py — All statistical analysis functions.
Each returns a list of FindingItem.
"""

import numpy as np
import pandas as pd
from typing import List

from app.models.schemas import FindingItem


def analyze_missing(df: pd.DataFrame) -> List[FindingItem]:
    findings = []
    total = len(df)
    missing = df.isnull().sum()
    cols = missing[missing > 0]

    if cols.empty:
        findings.append(FindingItem(label="Missing Values", value="None", note="Dataset is complete"))
    else:
        for col, count in cols.items():
            pct = round(count / total * 100, 1)
            sev = "High" if pct > 20 else "Medium" if pct > 5 else "Low"
            findings.append(FindingItem(
                label=f"Missing: {col}",
                value=f"{count} ({pct}%)",
                note=f"Severity: {sev}"
            ))
    return findings


def analyze_duplicates(df: pd.DataFrame) -> List[FindingItem]:
    count = int(df.duplicated().sum())
    pct = round(count / len(df) * 100, 2)
    return [FindingItem(
        label="Duplicate Rows",
        value=f"{count} ({pct}%)" if count > 0 else "None",
        note="Consider deduplication" if count > 0 else "No duplicates found"
    )]


def analyze_stats(df: pd.DataFrame) -> List[FindingItem]:
    findings = []
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        return findings

    for col in numeric.columns:
        s = numeric[col].describe()
        findings.append(FindingItem(
            label=f"Stats: {col}",
            value={
                "mean": round(float(s["mean"]), 4),
                "median": round(float(numeric[col].median()), 4),
                "std": round(float(s["std"]), 4),
                "min": round(float(s["min"]), 4),
                "max": round(float(s["max"]), 4),
            },
            note=f"{int(s['count'])} non-null values"
        ))
    return findings


def analyze_outliers(df: pd.DataFrame) -> List[FindingItem]:
    findings = []
    numeric = df.select_dtypes(include="number")

    for col in numeric.columns:
        series = numeric[col].dropna()
        if len(series) < 4:
            continue

        # IQR method
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        outliers_iqr = ((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum()

        # Z-score method
        if series.std() > 0:
            outliers_z = (np.abs((series - series.mean()) / series.std()) > 3).sum()
        else:
            outliers_z = 0

        if outliers_iqr > 0 or outliers_z > 0:
            pct = round(max(outliers_iqr, outliers_z) / len(series) * 100, 1)
            findings.append(FindingItem(
                label=f"Outliers: {col}",
                value=f"{max(outliers_iqr, outliers_z)} ({pct}%)",
                note=f"IQR: {int(outliers_iqr)}, Z-score: {int(outliers_z)}"
            ))

    if not findings:
        findings.append(FindingItem(label="Outliers", value="None detected", note="All columns within normal bounds"))
    return findings


def analyze_correlations(df: pd.DataFrame) -> List[FindingItem]:
    findings = []
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return findings

    corr = numeric.corr()
    cols = corr.columns.tolist()
    seen = set()

    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            pair = (cols[i], cols[j])
            if pair in seen:
                continue
            seen.add(pair)
            val = round(float(corr.iloc[i, j]), 3)
            if abs(val) >= 0.6:
                direction = "positive" if val > 0 else "negative"
                strength = "strong" if abs(val) >= 0.8 else "moderate"
                findings.append(FindingItem(
                    label=f"Correlation: {cols[i]} ↔ {cols[j]}",
                    value=f"r = {val}",
                    note=f"{strength.capitalize()} {direction} correlation"
                ))

    if not findings:
        findings.append(FindingItem(label="Correlations", value="None strong", note="No pairs exceed |r| = 0.6"))
    return findings


def analyze_categorical(df: pd.DataFrame) -> List[FindingItem]:
    findings = []
    cats = df.select_dtypes(include=["object", "category", "bool"]).columns

    for col in cats:
        series = df[col].dropna()
        unique = series.nunique()
        total = len(series)
        top = series.value_counts().idxmax() if not series.empty else "N/A"
        top_pct = round(series.value_counts().max() / total * 100, 1) if not series.empty else 0
        card_pct = round(unique / total * 100, 1)

        note = "Possible ID column" if card_pct > 90 else f"Top: '{top}' ({top_pct}%)"
        findings.append(FindingItem(
            label=f"Categorical: {col}",
            value=f"{unique} unique ({card_pct}% cardinality)",
            note=note
        ))
    return findings
