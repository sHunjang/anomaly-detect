"""
FastAPI 애플리케이션 진입점
실행: uvicorn app.main:app --realod
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.predict import router as predict_router
from app.models.inference import inference_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버가 시작될 때, 종료될 때 실행할 코드를 정의하는 곳
    yield 이전: 서버 시작 시 실행 (여기서 모델을 미리 로딩)
    yield 이후: 서버 종료 시 실행 (지금은 딱히 정리할 게 없어서 비워둠)
    """

    inference_service.load()
    yield
    print("서버 종료")


app = FastAPI(title="Anomaly Detection API", lifespan=lifespan)

# predict.py에서 정의한 라우터를 이 app에 연결
app.include_router(predict_router)

@app.get("/health")
def healt_check():
    """서버가 살아있는지 확인하는 엔드포인트."""
    return {"status": "ok"}