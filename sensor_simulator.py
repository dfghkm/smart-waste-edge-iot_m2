import numpy as np
import pandas as pd
from src.config import CONTAINERS


def generate_telemetry(days: int = 7, seed: int = 42) -> pd.DataFrame:
    """Генерує сирі дані сенсорів із додаванням аномальних викидів та пропусків."""
    np.random.seed(seed)
    timestamps = pd.date_range(start="2026-10-01 00:00:00", periods=days * 24, freq="h")
    records = []

    for c in CONTAINERS:
        fill = np.random.uniform(5.0, 15.0)
        for ts in timestamps:
            hour_factor = 1.3 if 8 <= ts.hour <= 21 else 0.4
            fill += np.random.uniform(0.3, 1.2) * c["rate"] * hour_factor

            # Імітація планового вивезення при заповненні >= 88%
            if fill >= 88.0:
                fill = np.random.uniform(2.0, 6.0)

            temp = (
                18.0
                + 6.5 * np.sin(2 * np.pi * (ts.hour - 6) / 24)
                + 0.08 * fill
                + np.random.normal(0, 0.8)
            )
            humidity = np.clip(
                55.0 + 0.25 * fill - 0.4 * (temp - 18.0) + np.random.normal(0, 2.5),
                30.0,
                98.0,
            )
            methane = np.clip(
                120.0
                + 4.8 * fill
                + 18.5 * max(0.0, temp - 15.0)
                + 1.2 * humidity
                + np.random.normal(0, 15.0),
                50.0,
                2500.0,
            )

            records.append([
                c["id"],
                ts.isoformat(),
                round(fill, 2),
                round(temp, 2),
                round(humidity, 2),
                round(methane, 2),
            ])

    df_raw = pd.DataFrame(
        records,
        columns=["container_id", "timestamp", "fill_level", "temperature", "humidity", "methane_ppm"],
    )

    # Ін'єкція 7% пропусків (NaN) та 5% імпульсних шумів
    for col in ["fill_level", "temperature", "humidity", "methane_ppm"]:
        nan_idx = np.random.choice(df_raw.index, size=int(0.07 * len(df_raw)), replace=False)
        df_raw.loc[nan_idx, col] = np.nan

        spike_idx = np.random.choice(df_raw.index, size=int(0.05 * len(df_raw)), replace=False)
        df_raw.loc[spike_idx, col] *= np.random.uniform(2.8, 4.5)

    return df_raw