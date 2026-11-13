"""
generate_synthetic_data.py

Generates a synthetic (fake) daily ICU bed capacity dataset for German
hospitals, used as raw input to the ingest -> anonymize -> dashboard
pipeline.

Methodology / assumptions (written down so it isn't a mystery in an
interview):
- 15 fictional hospitals across 2 German states (Nordrhein-Westfalen,
  Sachsen), loosely echoing DMI's real office locations (Muenster,
  Essen, Leisnig, Chemnitz).
- Each hospital has a fixed ICU bed capacity between 12 and 40, in line
  with typical mid-size German hospital ICU sizes.
- Daily occupancy rate per hospital is drawn from a Beta(7, 3) distribution
  (mean ~70%), plus a small weekday effect and daily noise.
- Data-quality problems are injected on purpose, so the ingestion script
  has real problems to catch instead of only ever seeing clean data:
    - ~3% of occupied-bed values are missing
    - ~1% are invalid (occupied > capacity, or negative)
    - ~1% extra duplicate rows are appended

This is SIMULATED data only. No real hospital or patient data is used.
"""

import os
import numpy as np
import pandas as pd

RNG_SEED = 42
N_DAYS = 90
OUTPUT_PATH = os.path.join("data", "raw", "icu_beds.csv")

HOSPITALS = [
    ("Klinikum Muenster Nord", "Nordrhein-Westfalen", 32),
    ("St. Elisabeth Hospital Muenster", "Nordrhein-Westfalen", 18),
    ("Universitaetsklinikum Essen", "Nordrhein-Westfalen", 40),
    ("Ev. Krankenhaus Essen-Werden", "Nordrhein-Westfalen", 22),
    ("Kreiskrankenhaus Leisnig", "Sachsen", 12),
    ("Klinikum Chemnitz", "Sachsen", 35),
    ("Diakonissenkrankenhaus Chemnitz", "Sachsen", 20),
    ("Klinikum Dortmund", "Nordrhein-Westfalen", 28),
    ("Marienhospital Bochum", "Nordrhein-Westfalen", 24),
    ("Krankenhaus Freiberg", "Sachsen", 15),
    ("St. Vincentius Koeln", "Nordrhein-Westfalen", 30),
    ("Uniklinikum Leipzig", "Sachsen", 38),
    ("Klinikum Dresden Friedrichstadt", "Sachsen", 33),
    ("Herz-Jesu-Krankenhaus Muenster", "Nordrhein-Westfalen", 16),
    ("Knappschaftskrankenhaus Essen", "Nordrhein-Westfalen", 26),
]


def generate():
    rng = np.random.default_rng(RNG_SEED)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=N_DAYS)

    rows = []
    for name, bundesland, capacity in HOSPITALS:
        base_rate = rng.beta(7, 3)  # this hospital's typical occupancy level
        for d in dates:
            weekday_boost = 0.03 if d.weekday() < 5 else -0.02
            noise = rng.normal(0, 0.06)
            rate = np.clip(base_rate + weekday_boost + noise, 0.05, 1.15)
            occupied = int(round(rate * capacity))
            rows.append({
                "date": d.strftime("%Y-%m-%d"),
                "hospital_name": name,
                "bundesland": bundesland,
                "bettenzahl_icu": capacity,
                "belegte_betten_icu": occupied,
            })

    df = pd.DataFrame(rows)

    # Inject missing values (~3%)
    missing_idx = rng.choice(df.index, size=int(0.03 * len(df)), replace=False)
    df.loc[missing_idx, "belegte_betten_icu"] = np.nan

    # Inject invalid values (~1%): occupied > capacity, or negative
    remaining = df.index.difference(missing_idx)
    invalid_idx = rng.choice(remaining, size=int(0.01 * len(df)), replace=False)
    for i in invalid_idx:
        if rng.random() < 0.5:
            df.loc[i, "belegte_betten_icu"] = df.loc[i, "bettenzahl_icu"] + rng.integers(1, 5)
        else:
            df.loc[i, "belegte_betten_icu"] = -rng.integers(1, 3)

    # Inject duplicate rows (~1%)
    dup_rows = df.sample(n=max(1, int(0.01 * len(df))), random_state=RNG_SEED)
    df = pd.concat([df, dup_rows], ignore_index=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Generated {len(df)} rows ({len(HOSPITALS)} hospitals x {N_DAYS} days, "
          f"plus injected duplicates) -> {OUTPUT_PATH}")


if __name__ == "__main__":
    generate()
