"""
ingest_data.py

Loads the raw ICU bed dataset, runs data-quality checks, and produces a
cleaned dataset. Every cleaning decision is deliberate and logged, so
nothing gets silently turned into a misleading value.
"""

import os
import numpy as np
import pandas as pd

RAW_PATH = os.path.join("data", "raw", "icu_beds.csv")
CLEAN_PATH = os.path.join("data", "processed", "icu_beds_clean.csv")
REPORT_PATH = os.path.join("data", "processed", "quality_report.txt")


def load_and_inspect_data(file_path):
    """Loads raw hospital CSV data and returns it with a printed overview."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found at {file_path}")

    df = pd.read_csv(file_path)
    print("=== RAW DATASET OVERVIEW ===")
    print(f"Total records: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    return df


def _standardize_columns(df):
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    return df


def validate_data_quality(df, capacity_col="bettenzahl_icu", occupied_col="belegte_betten_icu"):
    """
    Runs domain-specific quality checks and returns a report dict.
    This only measures problems -- clean_data() is what fixes them.
    """
    report = {"duplicate_rows": int(df.duplicated().sum())}

    missing = df.isna().sum()
    report["missing_by_column"] = {c: int(v) for c, v in missing.items() if v > 0}

    if capacity_col in df.columns and occupied_col in df.columns:
        negative_mask = (df[occupied_col] < 0) | (df[capacity_col] < 0)
        over_capacity_mask = df[occupied_col] > df[capacity_col]
        report["negative_values"] = int(negative_mask.sum())
        report["occupied_exceeds_capacity"] = int(over_capacity_mask.sum())

    return report


def clean_data(df, capacity_col="bettenzahl_icu", occupied_col="belegte_betten_icu"):
    """
    Cleans the dataset:
    - exact duplicate rows are dropped
    - impossible values (negative occupied, or occupied > capacity) are
      corrected and flagged in a boolean column, never silently zeroed
    - missing occupancy values are imputed using that specific hospital's
      own median occupancy RATE (not a flat 0, which would misrepresent an
      empty ICU as a real observation), and flagged so downstream users
      can tell real data from imputed data
    - remaining missing text values are filled with 'Unknown'
    """
    df = _standardize_columns(df)

    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Dropped {before - len(df)} exact duplicate rows.")

    if capacity_col in df.columns and occupied_col in df.columns:
        invalid_mask = (df[occupied_col] < 0) | (df[occupied_col] > df[capacity_col])
        df["occupied_was_corrected"] = invalid_mask.fillna(False)
        df.loc[df[occupied_col] < 0, occupied_col] = np.nan
        df.loc[df[occupied_col] > df[capacity_col], occupied_col] = np.nan

        if "hospital_name" in df.columns:
            occ_rate = df[occupied_col] / df[capacity_col]
            hospital_median_rate = occ_rate.groupby(df["hospital_name"]).transform("median")
            fill_rate = hospital_median_rate.fillna(occ_rate.median())
        else:
            fill_rate = pd.Series((df[occupied_col] / df[capacity_col]).median(), index=df.index)

        was_missing = df[occupied_col].isna()
        df["occupied_was_imputed"] = was_missing
        df.loc[was_missing, occupied_col] = (fill_rate[was_missing] * df.loc[was_missing, capacity_col]).round()
        df[occupied_col] = df[occupied_col].astype(int)

    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].fillna("Unknown")

    print(f"Records remaining after cleaning: {len(df)}")
    return df


def write_report(report, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("=== DATA QUALITY REPORT (pre-clean) ===\n")
        for key, value in report.items():
            f.write(f"{key}: {value}\n")
    print(f"Quality report written to {path}")


if __name__ == "__main__":
    raw_df = load_and_inspect_data(RAW_PATH)
    raw_df_std = _standardize_columns(raw_df)

    quality_report = validate_data_quality(raw_df_std)
    print("=== QUALITY CHECKS (pre-clean) ===")
    for k, v in quality_report.items():
        print(f"{k}: {v}")

    clean_df = clean_data(raw_df)

    os.makedirs(os.path.dirname(CLEAN_PATH), exist_ok=True)
    clean_df.to_csv(CLEAN_PATH, index=False)
    write_report(quality_report, REPORT_PATH)
    print(f"\nCleaned dataset saved to: {CLEAN_PATH}")
