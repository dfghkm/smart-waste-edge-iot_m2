from src.sensor_simulator import generate_telemetry
from src.edge_processor import clean_sensor_data, benchmark_compression
from src.database_manager import init_and_populate_db, fetch_joined_telemetry
from src.cloud_sync import upload_and_restore_from_firebase
from src.analytics_report import build_analytics_and_forecast


def run_pipeline() -> None:
    print("1. Генерація даних сенсорів із шумами та пропусками...")
    df_raw = generate_telemetry(days=7)

    print("2. Виконання Edge-очищення та інтерполяції...")
    df_clean = clean_sensor_data(df_raw)

    print("3. Збереження телеметрії у реляційну БД SQLite...")
    init_and_populate_db(df_clean)
    df_joined = fetch_joined_telemetry()

    print("4. Тестування алгоритмів стиснення на Edge-рівні...")
    df_comp, blobs, orig_size = benchmark_compression(df_clean)
    print(df_comp.to_string(index=False))

    print("\n5. Відправлення оптимального пакета (bzip2) у Firebase та зворотне завантаження...")
    df_cloud = upload_and_restore_from_firebase(blobs["bzip2"], orig_size)

    print("\n6. Побудова аналітичних графіків та фінального звіту...")
    build_analytics_and_forecast(df_joined, df_cloud)


if __name__ == "__main__":
    run_pipeline()