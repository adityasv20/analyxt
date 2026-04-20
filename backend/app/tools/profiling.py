"""tools/profiling.py — Dataset metadata extraction."""

import pandas as pd
from app.models.schemas import DatasetOverview


def profile_dataset(df: pd.DataFrame) -> DatasetOverview:
    numeric = df.select_dtypes(include="number").columns.tolist()
    categorical = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    missing = {col: int(n) for col, n in df.isnull().sum().items() if n > 0}
    dtypes = {col: str(dt) for col, dt in df.dtypes.items()}
    memory_kb = round(df.memory_usage(deep=True).sum() / 1024, 2)

    return DatasetOverview(
        rows=int(df.shape[0]),
        columns=int(df.shape[1]),
        column_names=df.columns.tolist(),
        dtypes=dtypes,
        missing_values=missing,
        duplicate_rows=int(df.duplicated().sum()),
        numeric_columns=numeric,
        categorical_columns=categorical,
        memory_usage_kb=memory_kb,
    )
