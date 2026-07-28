"""
학습된 Autoencoder 모델, Scaler, threshold를 파일로 저장
- 이렇게 저장하면, 나중에 API 서버가 매번 재학습 없이 바로 예측만 하면 됨
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch import nn
from train_autoencoder import (
    DATA_PATH,
    get_device,
    load_and_prepare_data,
    set_seed,
    train_autoencoder,
)

MODEL_DIR = Path(__file__).parent / "saved_models"


def save_artifacts(model: nn.Module, scaler: StandardScaler, threshold: float, input_dim: int):
    """
    모델, Scaler, threshold를 각각 적절한 형식으로 저장

    - 모델(PyTorch): .pth 확장자로 저장하는 것이 관례. state_dict()는 "학습된 가중치 값들"만 뽑아낸 것
        -> 모델 구조 코드(AnomalyAutoencoder 클래스)는 항상 같이 있어야 불러올 수 있음
    - scaler(scikit-learn): joblib으로 저장하는 게 표준 관례 (pickle 기반이지만 numpy 배열에 최적화됨)
    - threshold: 숫자 하나라 그냥 json으로 저장 (사람이 읽기도 쉬움)
    """

    MODEL_DIR.mkdir(exist_ok=True)

    torch.save(model.state_dict(), MODEL_DIR / "autoencoder.pth")
    joblib.dump(scaler, MODEL_DIR / "scaler.pkl")

    metadata = {"threshold": threshold, "input_dim": input_dim}
    with open(MODEL_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"저장 완료: {MODEL_DIR}")


if __name__ == "__main__":
    set_seed()

    device = get_device()
    df, X = load_and_prepare_data()

    # scaler를 따로 다시 얻어야 하지만, load_and_prepare_data 내부 로직을 여기서 한 번 더 노출
    # (지금 구조상 scaler가 함수 안에 갇혀있어서, 아래처럼 별도로 다시 fit함)
    feature_cols = ["value", "value_diff", "deviation_from_trend", "short_vs_long_trend"]
    df_raw = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])

    df_raw["value_diff"] = df_raw["value"].diff().fillna(0)
    df_raw["rolling_mean_30"] = df_raw["value"].rolling(window=30, min_periods=1).mean()
    df_raw["deviation_from_trend"] = df_raw["value"] - df_raw["rolling_mean_30"]
    df_raw["rolling_mean_200"] = df_raw["value"].rolling(window=200, min_periods=1).mean()
    df_raw["short_vs_long_trend"] = df_raw["rolling_mean_30"] - df_raw["rolling_mean_200"]

    scaler = StandardScaler()
    scaler.fit(df_raw[feature_cols].values)

    X_train_normal = X[df["is_anomaly"] == 0]
    model = train_autoencoder(X_train_normal, input_dim=X.shape[1], device=device)

    # threshold 계산 (train_autoencoder.py의 evaluate 로직과 동일한 방식)
    model.eval()
    X_tensor = torch.tensor(X, dtype=torch.float32).to(device)

    with torch.no_grad():
        reconstructed = model(X_tensor)

    reconstructed_error = torch.mean((X_tensor - reconstructed) ** 2, dim=1).cpu().numpy()
    threshold = float(np.percentile(reconstructed_error, 100 - 44))

    save_artifacts(model, scaler, threshold, input_dim=X.shape[1])