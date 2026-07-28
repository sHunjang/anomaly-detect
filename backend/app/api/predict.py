"""
/predict 엔드포인트 정의
"""

from fastapi import APIRouter

from app.models.inference import inference_service
from app.models.schemas import PredictRequest, PredictResponse

# APIRouter: main.py의 app과는 별개로, 관련된 엔드포인트끼리 묶어서 관리하는 용도
# 나중에 엔드포인트가 많아지면 (ex: /train, /history 등) 파일별로 나눠서 관리하기 좋음
router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    POST 요청으로 시계열 데이터 한 건을 받아서, 이상치 여부를 판전해 돌려줌

    request: PredictRequest 형식 자동 검증됨 (Pydantic이 처리)
    response_model=PredictResponse: 응답도 이 형식에 맞춰서 나가도록 강제
    """

    result = inference_service.predict(
        value=request.value,
        value_diff=request.value_diff,
        deviation_from_trend=request.deviation_from_trend,
        short_vs_long_trend=request.short_vs_long_trend
    )

    return result