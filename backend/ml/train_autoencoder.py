"""
Autoencoder 학습 및 평가
- 핵심 아이디어: 정상 데이터만으로 학습시켜서 "정상을 복원하는 법"만 배우게 함
- 학습이 끝나면 전체 데이터(정상+이상치)를 넣어보고, 복원 오차가 큰 것을 이상치로 판단
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

from autoencoder import AnomalyAutoencoder


DATA_PATH = Path(__file__).parent / "data" / "synthetic_timeseries.csv"


def get_device() -> torch.device:
    """
    M3 Pro에서 MPS(Apple의 GPU 가속)를 쓸 수 있는지 확인,
    가능하면 MPS, 안 되면 CPU 사용
    """

    if torch.backends.mps.is_available():
        return torch.device("mps")

    return torch.device("cpu")


def load_and_prepare_data():

    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])

    # Isolation Forest 때 썼던 것과 같은 feature 엔지니어링을 여기서도 사용
    df["value_diff"] = df["value"].diff().fillna(0)
    df["rolling_mean_30"] = df["value"].rolling(window=30, min_periods=1).mean()
    df["deviation_from_trend"] = df["value"] - df["rolling_mean_30"]
    df["rolling_mean_200"] = df["value"].rolling(window=200, min_periods=1).mean()
    df["short_vs_long_trend"] = df["rolling_mean_30"] - df["rolling_mean_200"]

    feature_cols = ["value", "value_diff", "deviation_from_trend", "short_vs_long_trend"]
    features = df[feature_cols].values

    # 신경망은 입력값의 스케일(크기)에 민감함. value는 100 근처, diff는 0 근처처럼
    # feature 마다 범위가 다르면 학습이 잘 안되므로, 평균 0 / 표준편차 1로 맞춰줌
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    return df, scaled_features


def train_autoencoder(X_train: np.ndarray, input_dim: int, device: torch.device):

    model = AnomalyAutoencoder(input_dim=input_dim, latent_dim=2).to(device)

    # MSELoss: 원본과 복원본의 차이를 "제곱해서 평규낸 값"으로 측정
    # 복원이 잘 될수록 이 값이 작아짐 -> 이게 우리가 최소화하려는 목표
    criterion = nn.MSELoss()

    # Adam: 신경망 학습에서 가장 널리 쓰이는 최적화 알고리즘
    # lr(learning rate): 한 번에 얼마나 크게 학습할지 정하는 값. 너무 크면 불안정, 너무 작으면 느림
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # numpy 배열을 PyTorch가 이해하는 tensor로 변환하고, 학습 장치(MPS/CPU)로 옮김
    X_tensor = torch.tensor(X_train, dtype=torch.float32).to(device)

    n_epochs = 200  # 전체 데이터를 몇 번 반복해서 학습할지
    model.train()   # 모델을 "학습 모드"로 설정 (드롭아웃 등이 있으면 이때 활성화 됨)

    for epoch in range(n_epochs):

        optimizer.zero_grad()       # 이전 스탭의 기울기(gradient) 초기화
        reconstructed = model(X_tensor)     # 순전파: 입력을 넣어서 복원값을 얻음
        loss = criterion(reconstructed, X_tensor)   # 원본과 복원본의 차이 계산

        loss.backward()     # 역전파: 이 차이를 줄이려면 각 가중치를 어떻게 바꿔야 할지 계산
        optimizer.step()    # 계산된 방향으로 실제 가중치를 업데이트

        if (epoch + 1) % 20 == 0:
            print(f"Epoch {epoch+1}/{n_epochs}, Loss: {loss.item():.4f}")

    return model


def evaluate(df: pd.DataFrame, model: AnomalyAutoencoder, X: np.ndarray, device: torch.device):

    model.eval()    # 평가 모드로 전환 (학습 때와 다르게 동작해야 하는 레이어들을 비활성화)

    X_tensor = torch.tensor(X, dtype=torch.float32).to(device)

    # 평가 시에는 기울기를 계산할 필요 없음 -> no_gred()로 감싸서 메모리/속도 절약
    with torch.no_grad():
        reconstructed = model(X_tensor)


    # 각 데이터 포인트마다 "원본과 복원본이 얼마나 다른지" 계산 (feature별 차이의 제곱 평균)
    reconstructed_error = torch.mean((X_tensor - reconstructed) ** 2, dim=1)
    reconstructed_error = reconstructed_error.cpu().numpy()     # 다시 numpy 변환

    df["reconstructed_error"] = reconstructed_error


    # 임계값(threshold): 복원 오차가 이 값보다 크면 이상치로 판단
    # 여기서는 "상위 44%가 이상치"라는 실제 비율을 참고해서 백분위수로 임계값을 정함
    threshold = np.percentile(reconstructed_error, 100 - 44)
    df["predicted_anomaly"] = (reconstructed_error > threshold).astype(int)


    print(f"\n임계값(Threshold): {threshold:.4f}")
    print("\n=== 혼동 행렬 ===")
    print(confusion_matrix(df["is_anomaly"], df["predicted_anomaly"]))

    print("\n=== 상세 리포트 ===")
    print(classification_report(df["is_anomaly"], df["predicted_anomaly"], target_names=["normal", "anomaly"]))

    print("\n=== 이상치 타입별 탐지율 ===")
    for anomaly_type in ["spike", "drift", "level_shift"]:
        subset = df[df["anomaly_type"] == anomaly_type]

        if len(subset) == 0:
            continue

        detected_ratio = subset["predicted_anomaly"].mean()

        print(f"{anomaly_type}: {detected_ratio:.1f} 탐지됨 (총 {len(subset)}개 중)")

    return df


if __name__ == "__main__":

    device = get_device()
    print(f"사용 장치: {device}")

    df, X = load_and_prepare_data()

    # 정상 데이터만 골라서 학습용으로 사용 (Autoencoder 핵심: 정상만 보고 배움)
    X_train_normal = X[df["is_anomaly"] == 0]
    print(f"학습에 사용할 정상 데이터: {len(X_train_normal)}개")

    model = train_autoencoder(X_train_normal, input_dim=X.shape[1], device=device)


    # 평가는 정상+이상치 전체 데이터로 진행
    result_df = evaluate(df, model, X, device)

    output_path = Path(__file__).parent / "data" / "autoencoder_result.csv"
    result_df.to_csv(output_path, index=False)

    print(f"\n결과 저장 완료: {output_path}")