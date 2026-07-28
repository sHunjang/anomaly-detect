"""
FastAPI 애플리케이션 진입점
실행: uvicorn app.main:app --realod
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.predict import router as predict_router
from app.api.stream import router as stream_router
from app.models.inference import inference_service
from app.streaming.consumer import run_consumer_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버가 시작될 때, 종료될 때 실행할 코드를 정의하는 곳
    yield 이전: 서버 시작 시 실행 (여기서 모델을 미리 로딩)
    yield 이후: 서버 종료 시 실행 (지금은 딱히 정리할 게 없어서 비워둠)
    """
    inference_service.load()

    # 서버 시작과 동시에, Redis Stream을 계속 읽는 작업을 "백그라운드"에서 실행
    # create_task: 이 작업이 끝나길 기다리지 않고, 동시에 다른 요청도 처리할 수 있게 함
    consumer_task = asyncio.create_task(run_consumer_loop()) # noqa: F841

    yield
    print("서버 종료")


app = FastAPI(title="Anomaly Detection API", lifespan=lifespan)


# CORS 설정: 브라우저는 기본적으로 "다른 출처(origin)"로의 요청을 막음
# 프론트(localhost:5173)와 백엔드(localhost:8000)는 포트가 달라서 다른 출처로 취급됨
# 이 설정이 없으면 브라우저가 보안상 요청을 차단해버림
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# predict.py에서 정의한 라우터를 이 app에 연결
app.include_router(predict_router)

# stream.py에서 정의한 라우터를 app에 연결
app.include_router(stream_router)

@app.get("/health")
def healt_check():
    """서버가 살아있는지 확인하는 엔드포인트."""
    return {"status": "ok"}