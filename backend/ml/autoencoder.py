"""
PyTorch로 구현한 간단한 Autoencoder
- 입력을 점점 좁은 차원으로 압축(encoder)했다가 다시 원래 차원으로 복원(decoder)
- 정상 데이터로만 학습시켜서, 정상 패턴을 "기억"하게 만드는 것이 목적
"""

from typing import Any

import torch.nn as nn


class AnomalyAutoencoder(nn.Module):
    def __init__(self, input_dim: int, latent_dim: int = 2):
        """
        - input_dim: 입력 feature 개수 (Isolation Froest 때 만든 feature 개수와 맞춤)
        - latent_dim: 가장 압축된 지점(잠재 공간)의 차원. 작을수록 더 강하게 압축됨
        """

        super().__init__()

        # Encoder: input_dim -> 점점 좁아짐 -> latent_dim
        # nn.Sequential == 레이어들을 순서대로 통과시켜주는 컨테이너
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 8),    # 완전연결층: input_dim개 값을 받아 8개로 변환
            nn.ReLU(),                  # 활성화 함수: 비선형성을 추가해서 복잡한 패턴도 학습 가능하도록 구성
            nn.Linear(8, 4),
            nn.ReLU(),
            nn.Linear(4, latent_dim),   # 가장 좁은 지점 (잠재 공간)
        )

        # Decoder: latent_dim -> 점점 넓어짐 -> input_dim (원본 크기로 복원)
        # Encoder와 대칭되는 구조
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 4),
            nn.ReLU(),
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, input_dim),    # 원본과 같은 크기로 복원
        )

    def forward(self, x):
        """
        - forward: 데이터가 모델을 통과할 때 실제로 실행되는 계산 흐름을 정의
        - PyTorchsms model(x)로 호출하면 이 forward()가 자동으로 실행됨
        """
        encoded = self.encoder(x)   # 압축
        decoded = self.decoder(encoded)    # 복원

        return decoded
    