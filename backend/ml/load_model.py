"""
저장된 모델/scaler/threshold를 불러와서, 새 데이터에 대해 예측하는 함수 제공
- API 서버에는 이 load_artifacts()를 서버 시작 시 딱 한 번만 호출하고,
    이후 요청이 올 때마다 predict()만 반복 호출하는 구조가 될 것
"""

import json
from pathlib import Path

import joblib
import numpy as np
import torch
from autoencoder import AnomalyAutoencoder

MODEL_DIR = Path(__file__).parent / "saved_models"


def load_artifacts(device: torch.device):
    with open(MODEL_DIR / "metadata.json") as f:
        metadata = json.load(f)

    model = AnomalyAutoencoder(input_dim=metadata["input_dim"], latent_dim=2).to(device)

    # state_dict를 불러와서 모델에 채워 넣음 (모델 "틀"은 코드로, 가중치 "내용들"은 파일에서)
    model.load_state_dict(torch.load(MODEL_DIR / "autoencoder.pth", map_location=device))
    model.eval()    # 불러온 직후 바로 평가 모드 설정 (추론만 할거임)

    scaler = joblib.load(MODEL_DIR / "scaler.pkl")
    threshold = metadata["threshold"]

    return model, scaler, threshold


def predict(model, scaler, threshold: float, feature_row: np.ndarray, device: torch.device) -> dict:
    """
    새로운 데이터 한 건(feature_row)에 대해 이상 여부를 판정
    
    - feature_row: [value, value_diff, deviation_from_trend, short_vs_long_trend] 형태의 1차원 배열
    """
    scaled = scaler.transform(feature_row.reshape(1, -1))
    X_tensor = torch.tensor(scaled, dtype=torch.float32).to(device)

    with torch.no_grad():
        reconstructed = model(X_tensor)

    error = torch.mean((X_tensor - reconstructed) ** 2).item()
    is_anomaly = error > threshold

    return {
        "reconstructed_error": error,
        "threshold": threshold,
        "is_anomaly": bool(is_anomaly),
    }


if __name__ == "__main__":

    # 간단한 동작 테스트: 저장된 모델을 불러와서, 임의의 값 하나를 넣어봄
    device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
    model, scaler, threshold = load_artifacts(device)

    # 테스트용 정상적인 값 하나 (대략 threshold 근처)
    test_input = np.array([105.0, 0.5, 2.0, 1.0])
    result = predict(model, scaler, threshold, test_input, device)
    print("정상 예시 테스트: ", result)

    # 테스트용 이상치 값 하나 (스파이크 흉내)
    test_input_anomaly = np.array([450.0, 300.0, 340.0, 300.0])
    result = predict(model, scaler, threshold, test_input_anomaly, device)
    print("이상치 예시 테스트: ", result)
