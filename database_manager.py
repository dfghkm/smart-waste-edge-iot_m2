import os
import sqlite3
import pandas as pd
from src.config import CONTAINERS, DB_PATH


def init_and_populate_db(df_clean: pd.DataFrame, db_path: str = DB_PATH) -> None:
    """Створює реляційну БД SQLite (3 таблиці з FOREIGN KEY) та записує очищену телеметрію."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.executescript("""
        DROP TABLE IF EXISTS telemetry;
        DROP TABLE IF EXISTS sensors;
        DROP TABLE IF EXISTS containers;

        CREATE TABLE containers (
            container_id INTEGER PRIMARY KEY,
            location TEXT NOT NULL,
            capacity_liters INTEGER NOT NULL
        );

        CREATE TABLE sensors (
            sensor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            container_id INTEGER NOT NULL,
            sensor_type TEXT NOT NULL,
            unit TEXT NOT NULL,
            FOREIGN KEY (container_id) REFERENCES containers(container_id)
        );

        CREATE TABLE telemetry (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            container_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            fill_level REAL NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            methane_ppm REAL NOT NULL,
            FOREIGN KEY (container_id) REFERENCES containers(container_id)
        );
    """)

    cursor.executemany(
        "INSERT INTO containers (container_id, location, capacity_liters) VALUES (?, ?, ?)",
        [(c["id"], c["location"], c["capacity_l"]) for c in CONTAINERS],
    )

    sensor_meta = [
        ("ultrasonic_fill", "%"),
        ("dht22_temp", "°C"),
        ("dht22_hum", "%"),
        ("mq4_methane", "ppm"),
    ]
    for c in CONTAINERS:
        for stype, unit in sensor_meta:
            cursor.execute(
                "INSERT INTO sensors (container_id, sensor_type, unit) VALUES (?, ?, ?)",
                (c["id"], stype, unit),
            )

    df_clean.to_sql("telemetry", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def fetch_joined_telemetry(db_path: str = DB_PATH) -> pd.DataFrame:
    """Повертає об'єднану вибірку телеметрії та довідника локацій через SQL JOIN."""
    conn = sqlite3.connect(db_path)
    query = """
        SELECT t.*, c.location, c.capacity_liters
        FROM telemetry t
        JOIN containers c ON t.container_id = c.container_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df