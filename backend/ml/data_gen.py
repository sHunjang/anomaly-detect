"""
더미 시계열 데이터 생성
- 기본 신호: sin 파형 + 노이즈 (24시간 주기)
- 이상치 3종: 스파이크, 드리프트, 레벨 시프트
- 결과: CSV 저장 (timestamp, value, is_anomaly, anomaly_type)
"""

from pathlib import Path

import numpy as np
import pandas as pd

# 재현 가능하게 랜덤 시드 고정 - 매번 같은 데이터가 나오게 함
np.random.seed(42)


def generate_base_single(n_points: int, period: int = 1440) -> np.ndarray:
    """
    정상적인 배경 신호 생성
    
    n_points: 전체 데이터 포인트 개수 (ex: 1440 = 1분 간격으로 하루치)
    period: 주기 (기본 1440 = 하루를 1분 단위로 쪼갠 것)
    """

    t = np.arange(n_points)

    # sin 파형: 1440을 중심으로 ±15 정도 오르내림 (낮/밤 패턴 흉내)
    base = 100 + 15 * np.sin(2 * np.pi * t / period)

    # 약간의 랜덤 노이즈 추가 (완전히 매끈하면 비현실적)
    noise = np.random.normal(0, 2, n_points)

    return base + noise


def inject_spikes(values: np.ndarray, labels: np.ndarray, types: list, zone: tuple, ratio: float = 0.01):
    """스파이크: zone 범위 안에서, 랜덤 시점에 값을 3~5배로 순간 튀게 함"""

    zone_start, zone_end = zone
    zone_size = zone_end - zone_start
    n_spikes = int(zone_size * ratio * 3)   # zone이 좁아졌으니 비율 좀 높여줌 (개수 확보용)

    spike_indices = np.random.choice(range(zone_start, zone_end), n_spikes, replace=False)

    for idx in spike_indices:
        multiplier = np.random.uniform(3, 5)

        values[idx] *= multiplier
        labels[idx] = 1
        types[idx] = "spike"

    return values, labels, types


def inject_drift(values: np.ndarray, labels: np.ndarray, types: list, zone: tuple, ratio: float = 0.3):
    """
    드리프트: zone 범위 안에서 서서히 20% 증가했다가 원래대로 돌아옴
    """

    zone_start, zone_end = zone
    zon_size = zone_end - zone_start
    drift_len = int(zon_size * ratio)

    # zone 안에서만 시작점을 고름 (drift_len만큼 공간이 남도록)
    start = np.random.randint(zone_start, zone_end - drift_len)

    # 0 -> 20% 증가 -> 다시 0으로 돌아오는 삼각형 모양 증가폭 만들기
    half = drift_len // 2

    # linspace(start, stop, num) 함수 == 지정한 시작점과 끝점 사이를 균등한 간격으로 나눈 숫자들을 1차원 배열로 생성
    ramp_up = np.linspace(0, 0.2, half)
    ramp_down = np.linspace(0.2, 0, drift_len - half)

    # concatenate((a, b), axis=0) == 배열 합치기. 
    # Numpy 배열을 특정 축(axis) 기준으로 합칠 때 사용. axis=0: 행 방향(위아래)으로 배열 연결, axis=1: 열 방향(양옆)으로 배열 연결
    drift_curve = np.concatenate([ramp_up, ramp_down])

    for offset, factor in enumerate(drift_curve):
        idx = start + offset
        values[idx] *= (1 + factor)
        labels[idx] = 1
        types[idx] = "drift"

    return values, labels, types


def inject_level_shift(values: np.ndarray, labels: np.ndarray, types: list, zone:tuple):
    """
    레벨 시프트: zone 시작점부터 zone 끝까지 기준선이 30% 영구적으로 이동
    """

    zone_start, zone_end = zone

    values[zone_start:zone_end] *= 1.3
    labels[zone_start:zone_end] = 1

    for i in range(zone_start, zone_end):
        types[i] = "level_shift"

    return values, labels, types


def generate_dataset(n_points: int = 4320) -> pd.DataFrame:
    """
    전체 데이터셋 생성 (default: 3일치, 1분 간격)
    """

    values = generate_base_single(n_points)

    baseline = values.copy()    # 이상치 주입 전 원본을 따로 보관 (나중에 잔차 계산용)

    labels = np.zeros(n_points, dtype=int)
    types = ["normal"] * n_points

    # 이상 현상이 겹치지 않도록 구간을 미리 3등분해서 각 이상치를 그 안에서만 생성
    spike_zone = (0, n_points // 3)
    drift_zone = (n_points // 3, 2 * n_points // 3)
    level_shift_zone = (2 * n_points // 3, n_points)

    values, labels, types = inject_spikes(values, labels, types, zone=spike_zone)
    values, labels, types = inject_drift(values, labels, types, zone=drift_zone)
    values, labels, types = inject_level_shift(values, labels, types, zone=level_shift_zone)

    timestamps = pd.date_range(start="2026-07-01", periods=n_points, freq="1min")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "value": values,
        "baseline": baseline,
        "is_anomaly": labels,
        "anomaly_type": types,
    })

    return df


if __name__ == "__main__":

    df = generate_dataset()

    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "synthetic_timeseries.csv"

    df.to_csv(output_path, index=False)

    print(f"생성 완료: {output_path}")
    print(f"전체 {len(df)}개 중 이상치 {df['is_anomaly'].sum()}개")
    print(df["anomaly_type"].value_counts())