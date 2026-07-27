"""
생성된 시계열 데이터 시각화
- 정상 신호는 실선
- 이상치는 타입별로 다른 색 점으로 표시
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "synthetic_timeseries.csv"

# 이상치 타입별 생상 지정
COLORS = {
    "spike": "red",
    "drift": "orange",
    "level_shift": "purple",
}


def plot_timeseries(df: pd.DataFrame, save_path: Path):

    # 잔차 계산: 실제값 - baseline
    df["residual"] = df["value"] - df["baseline"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8), sharex=True)

    # 전체 배경 신호 - 얇은 회색 선
    # 이상치 타입별로 겹쳐서 점 찍기 == 기존 원본 값 그래프
    ax1.plot(df["timestamp"], df["value"], color="lightgrey", linewidth=0.8, label="normal", zorder=1)
    for anomaly_type, color in COLORS.items():
        subset = df[df["anomaly_type"] == anomaly_type]
        ax1.scatter(subset["timestamp"], subset["value"], color=color, s=8, label=anomaly_type, zorder=2)

    ax1.set_title("Syncthetic time series with injected anomalies")
    ax1.set_xlabel("timestamp")
    ax1.set_ylabel("value")
    ax1.legend(loc="upper left")

    # 잔차 그래프 (baseline과 차이)
    ax2.plot(df["timestamp"], df["residual"], color="lightgrey", linewidth=0.8, zorder=1)
    for anomaly_type, color in COLORS.items():
        subset = df[df["anomaly_type"] == anomaly_type]
        ax2.scatter(subset["timestamp"], subset["residual"], color=color, s=8, zorder=2)
    ax2.axhline(0, color="black", linewidth=0.5, linestyle="--")    # 0 기준선
    ax2.set_title("Residual (value - baseline)")
    ax2.set_xlabel("timestamp")
    ax2.set_ylabel("residual")

    fig.tight_layout()

    fig.savefig(save_path, dpi=120)

    print(f"저장 완료: {save_path}")


if __name__ == "__main__":

    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])

    output_path = Path(__file__).parent / "data" / "timeseries_plot.png"
    plot_timeseries(df, output_path)