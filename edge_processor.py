import time
import gzip
import zlib
import bz2
import numpy as np
import pandas as pd
from src.config import SENSOR_LIMITS


def clean_sensor_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Периферійна очистка: відсікання викидів медіанним фільтром та інтерполяція пропусків."""
    df_clean = df_raw.copy()

    for _, group in df_clean.groupby("container_id"):
        idx = group.index
        for col, (low, high) in SENSOR_LIMITS.items():
            series = df_clean.loc[idx, col].copy()
            series[(series < low) | (series > high)] = np.nan

            median_trend = series.rolling(window=5, center=True, min_periods=1).median()
            outliers = np.abs(series - median_trend) > (3.5 * median_trend.std() + 1e-5)
            series[outliers] = np.nan

            series = series.interpolate(method="linear").bfill().ffill()
            df_clean.loc[idx, col] = np.round(series, 2)

    return df_clean


def benchmark_compression(df_clean: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, bytes], int]:
    """Порівняння ефективності алгоритмів стиснення gzip, zlib та bzip2."""
    payload_bytes = df_clean.to_json(orient="records").encode("utf-8")
    orig_size = len(payload_bytes)

    algorithms = {
        "gzip":  lambda d: gzip.compress(d, compresslevel=9),
        "zlib":  lambda d: zlib.compress(d, level=9),
        "bzip2": lambda d: bz2.compress(d, compresslevel=9),
    }

    stats = []
    blobs = {}

    for name, compress_fn in algorithms.items():
        t_start = time.perf_counter()
        compressed = compress_fn(payload_bytes)
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        blobs[name] = compressed
        stats.append({
            "Алгоритм": name,
            "Вихідний розмір (Б)": orig_size,
            "Стиснений розмір (Б)": len(compressed),
            "Коефіцієнт стиснення": round(orig_size / len(compressed), 2),
            "Економія трафіку (%)": round((1.0 - len(compressed) / orig_size) * 100.0, 2),
            "Час стиснення (мс)": round(elapsed_ms, 3),
        })

    return pd.DataFrame(stats), blobs, orig_size