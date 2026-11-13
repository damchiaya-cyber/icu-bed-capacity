"""
anonymize.py

Anonymizes hospital identifiers (DSGVO-style pseudonymization) and computes
the capacity metrics the dashboard uses for resource-allocation decisions.

Anonymization approach:
- The real identifying column (hospital_name) is hashed with SHA-256 into a
  short facility_hash. The mapping is one-way here; a real deployment would
  keep any reversible mapping in a separate, access-controlled store.
- The original hospital_name column is DROPPED from the output -- keeping
  it next to the hash would defeat the point of hashing it.
- bundesland (state) is kept: it's coarse enough that it doesn't
  re-identify a single facility on its own.
- A lightweight k-anonymity check warns if any (bundesland, date) group has
  fewer than K_THRESHOLD distinct facilities, since small groups are easier
  to re-identify even after hashing individual names.
"""

import hashlib
import os
import pandas as pd

CLEAN_PATH = os.path.join("data", "processed", "icu_beds_clean.csv")
ANON_PATH = os.path.join("data", "processed", "icu_beds_anonymized.csv")

K_THRESHOLD = 3
OCCUPANCY_ALERT_THRESHOLD = 0.90  # flag facility-days at/above 90% occupancy


def hash_identifier(value):
    """SHA-256 hash of a value, truncated to 12 hex chars for readability."""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def anonymize_and_enrich_data(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Clean dataset not found at {file_path}")

    df = pd.read_csv(file_path)

    if "hospital_name" not in df.columns:
        raise KeyError("Expected an identifying 'hospital_name' column to anonymize.")

    # 1. Pseudonymize the real identifier, then drop the original
    df["facility_hash"] = df["hospital_name"].apply(hash_identifier)
    df = df.drop(columns=["hospital_name"])

    # 2. k-anonymity sanity check on the remaining quasi-identifiers
    if "bundesland" in df.columns and "date" in df.columns:
        group_sizes = df.groupby(["bundesland", "date"])["facility_hash"].nunique()
        small_groups = group_sizes[group_sizes < K_THRESHOLD]
        if len(small_groups) > 0:
            print(f"WARNING: {len(small_groups)} (bundesland, date) groups have fewer than "
                  f"{K_THRESHOLD} distinct facilities -- these rows are more re-identifiable "
                  f"and would need further generalization in a real deployment.")

    # 3. Resource-allocation / capacity metrics
    bed_cols = [c for c in df.columns if "bett" in c or "capacity" in c]
    occ_cols = [c for c in df.columns if "belegt" in c or "occupied" in c]

    if bed_cols and occ_cols:
        capacity_col, occupied_col = bed_cols[0], occ_cols[0]
        df["occupancy_rate"] = (df[occupied_col] / df[capacity_col]).round(3)
        df["available_beds"] = df[capacity_col] - df[occupied_col]
        df["over_threshold"] = df["occupancy_rate"] >= OCCUPANCY_ALERT_THRESHOLD
    else:
        print("WARNING: capacity/occupied columns not found -- skipping occupancy metrics.")

    print("=== ANONYMIZATION + ENRICHMENT COMPLETE ===")
    print(f"Facilities anonymized: {df['facility_hash'].nunique()}")
    if "over_threshold" in df.columns:
        print(f"Facility-days at/above {int(OCCUPANCY_ALERT_THRESHOLD*100)}% occupancy: {df['over_threshold'].sum()}")

    return df


if __name__ == "__main__":
    anonymized_df = anonymize_and_enrich_data(CLEAN_PATH)
    os.makedirs(os.path.dirname(ANON_PATH), exist_ok=True)
    anonymized_df.to_csv(ANON_PATH, index=False)
    print(f"\nAnonymized & processed dataset saved to: {ANON_PATH}")
