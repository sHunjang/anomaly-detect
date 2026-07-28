"""
ml/load_model.py의 로직을 API 서버에서 쓰기 좋게 감싼 모듈
- 서버가 켜질 때 딱 한 번만 모델을 불러오고, 이후 요청마다 재사용
    (매 요청마다 모델을 다시 불러오면 매우 느림)
"""

import sys
from pathlib import Path

import numpy as np
import torch

# ml 폴더의 코드(load_model.py, autoencoder.py)를 import 하기 위해 경로 추가
ML_DIR = Path(__file__).parent.parent.parent / "ml"
sys.path.append(str(ML_DIR))


# 여기선 sys.path.append를 먼저 실행한 다음에 import해야 해서 어쩔 수 없이 순서가 꼬임.
#
from load_model import load_artifacts
from load_model import predict as run_prediction


class InferenceService:
    """
    모델/scaler/threshold를 멤버 변수로 들고 있다가, predict()가 호출되면
    이미 로딩된 것들을 재사용해서 빠르게 예측만 수행하는 클래스
    """

    def __init__(self):
        self.device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
        self.model = None
        self.scaler = None
        self.threshold = None

    def load(self):
        """서버 시작 시 한 번 호출해서 모델을 메모리에 올려둠"""
        self.model, self.scaler, self.threshold = load_artifacts(self.device)
        print(f"모델 로딩 완료 (device: {self.device})")

    def predict(self, value: float, value_diff: float, deviation_from_trend: float, short_vs_long_trend: float) -> dict:
        feature_row = np.array([value, value_diff, deviation_from_trend, short_vs_long_trend])
        return run_prediction(self.model, self.scaler, self.threshold, feature_row, self.device)


# 모듈 전체에서 하나만 존재하는 인스턴스 (싱글턴 패턴)
# main.py에서 서버 시작 시 이 인스턴스의 load()를 호출하고,
# predict.py에서는 이미 로딩된 이 인스턴스를 그대로 가져다 씀
inference_service = InferenceService()