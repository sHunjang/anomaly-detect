"""
API가 주고받을 데이터의 형태(스키마)를 정의
Pydantic 모델을 쓰면, FastAPI가 자동으로:
- 요청 데이터가 이 형식에 맞는지 검증 (틀리면 자동으로 에러 응답)
- API 문서(Swagger)도 자동으로 만들어줌
"""

from pydantic import BaseModel


class PredictRequest(BaseModel):
    """클라이언트가 예측을 요청할 때 보내는 데이터 형식"""

    value: float
    value_diff: float
    deviation_from_trend: float
    short_vs_long_trend: float


class PredictResponse(BaseModel):
    """서버가 돌려주는 예측 결과 형식"""

    is_anomaly: bool
    reconstructed_error: float
    threshold: float
