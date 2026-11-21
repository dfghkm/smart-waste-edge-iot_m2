import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from src.config import COLLECTION_THRESHOLD_PCT, METHANE_ALERT_PPM, REPORT_IMAGE_PATH


def build_analytics_and_forecast(df_joined: pd.DataFrame, df_cloud: pd.DataFrame) -> None:
    """Будує графіки аналітики, обчислює прогноз вивезення та виводить звіт за даними з хмари."""
    df_joined = df_joined.copy()
    df_joined["timestamp"] = pd.to_datetime(df_joined["timestamp"])

    corr_temp_ch4 = df_joined["temperature"].corr(df_joined["methane_ppm"])
    print(f"\nКоефіцієнт кореляції Пірсона (Температура <-> Метан): r = {corr_temp_ch4:.3f}")

    # Прогноз часу досягнення порогу 85%
    print("\nПРОГНОЗ ГРАФІКА ВИВЕЗЕННЯ ВІДХОДІВ")
    for loc, grp in df_joined.groupby("location"):
        grp = grp.sort_values("timestamp")
        drops = grp.index[grp["fill_level"].diff() < -40].tolist()
        last_cycle = grp.loc[drops[-1]:] if drops else grp

        hours = (last_cycle["timestamp"] - last_cycle["timestamp"].iloc[0]).dt.total_seconds() / 3600.0
        model = LinearRegression().fit(hours.values.reshape(-1, 1), last_cycle["fill_level"].values)
        rate = float(model.coef_[0])
        current_fill = float(last_cycle["fill_level"].iloc[-1])

        hours_left = max(0.0, (COLLECTION_THRESHOLD_PCT - current_fill) / (rate + 1e-6))
        eta = last_cycle["timestamp"].iloc[-1] + pd.Timedelta(hours=hours_left)
        print(f"• {loc}: заповнено {current_fill:.1f}% (+{rate:.2f}%/год) -> Вивезення: {eta:%Y-%m-%d %H:%M}")

    # Візуалізація 3 графіків
    os.makedirs(os.path.dirname(REPORT_IMAGE_PATH), exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for loc, grp in df_joined.groupby("location"):
        axes[0].plot(grp["timestamp"], grp["fill_level"], label=loc)
    axes[0].axhline(COLLECTION_THRESHOLD_PCT, color="red", linestyle="--", label="Поріг вивезення (85%)")
    axes[0].set_title("Динаміка заповнення контейнерів")
    axes[0].set_ylabel("Рівень заповнення, %")
    axes[0].tick_params(axis="x", rotation=30)
    axes[0].legend(fontsize=8)

    sns.regplot(
        data=df_joined,
        x="temperature",
        y="methane_ppm",
        ax=axes[1],
        scatter_kws={"alpha": 0.4, "color": "teal"},
        line_kws={"color": "darkred"},
    )
    axes[1].set_title(f"Кореляція Температура — Метан (r = {corr_temp_ch4:.2f})")
    axes[1].set_xlabel("Температура в контейнері, °C")
    axes[1].set_ylabel("Концентрація CH4, ppm")

    corr_matrix = df_joined[["fill_level", "temperature", "humidity", "methane_ppm"]].corr()
    sns.heatmap(corr_matrix, annot=True, cmap="YlGnBu", fmt=".2f", ax=axes[2])
    axes[2].set_title("Матриця кореляцій сенсорів")

    plt.tight_layout()
    plt.savefig(REPORT_IMAGE_PATH, dpi=150)
    plt.close(fig)

    # Узагальнений статистичний звіт на основі даних, завантажених із Firebase
    summary = df_cloud.groupby("container_id").agg(
        Середнє_заповнення_pct=("fill_level", "mean"),
        Макс_заповнення_pct=("fill_level", "max"),
        Середня_температура_C=("temperature", "mean"),
        Середня_вологість_pct=("humidity", "mean"),
        Макс_метан_ppm=("methane_ppm", "max"),
        Тривог_CH4_понад_800ppm=("methane_ppm", lambda x: (x > METHANE_ALERT_PPM).sum()),
    ).round(2)

    print("\nУЗАГАЛЬНЕНИЙ СТАТИСТИЧНИЙ ЗВІТ (З ДАНИХ FIREBASE)")
    print(summary.to_string())