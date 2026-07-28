"""
Redis Stream에서 새로 들어온 데이터를 읽어와 예측하고,
WebSocket으로 연결된 프론트엔드에 실시간 전달하는 백그라운드 태스트
"""

import asyncio
from datetime import datetime, timezone

import redis
import requests

from app.streaming.manager import manager

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

STREAM_NAME = "sensor-stream"
PREDICT_URL = "http://localhost:8000/predict"


def build_features(value: float, last_raw_value: float | None, clean_values: list[float]) -> dict:
    """
    - last_raw_value: 직전에 실제로 들어온 값 (정상/이상치 상관없이) -> value_diff 계산용
        스파이크 바로 다음 값이 살짝 이상하게 잡히는 건 의도된 정상 동작이라 그대로 둠
    - clean_values: 지금까지 "정상"으로 판정된 값들만 모아둔 기록 -> rolling mean 계산용
        이상치가 여기 섞이면 평균 자체가 오염돼서, 그 뒤로 30번 동안 계속 여파가 남기 때문에
        의도적으로 이상치는 제외하고 "깨끗한 기준선"만 유지함
    """

    if last_raw_value is None:
        value_diff = 0.0
    else:
        value_diff = value - last_raw_value


    if len(clean_values) == 0:
        rolling_mean_30 = value
        rolling_mean_200 = value
    else:
        window_30 = clean_values[-30:]
        window_200 = clean_values[-200:]
        rolling_mean_30 = sum(window_30) / len(window_30)
        rolling_mean_200 = sum(window_200) / len(window_200)

    deviation_from_trend = value - rolling_mean_30
    short_vs_long_trend = rolling_mean_30 - rolling_mean_200

    return {
        "value": value,
        "value_diff": value_diff,
        "deviation_from_trend": deviation_from_trend,
        "short_vs_long_trend": short_vs_long_trend
    }


def call_predict_api(features: dict) -> dict:
    """
    FastAPI 서버에 실제 HTTP POST 요청을 보내서 예측 결과를 받아옴
    """
    response = requests.post(PREDICT_URL, json=features, timeout=5)
    response.raise_for_status()     # 200이 아니면 예외 발생 (에러 상황을 조용히 넘기지 않기 위함)
    return response.json()


async def run_consumer_loop():
    """
    기존 run_consumer()와 로직은 같지만, async 함수로 바꿔서
    FastAPI 서버 안에서 다른 요청 처리를 막지 않고 "백그라운드에서" 계속 돌게 함
    """
    print(f"백그라운드 Consumer 시작 - '{STREAM_NAME}' 구독 중...")

    # "$"는 "지금 이 순간 이후에 새로 들어오는 것부터 읽겠다"라는 뜻
    # (스트림에 이미 쌓여있던 과거 데이터는 버리고, 새로 들어오는 것만 봄)
    last_id = "$"
    last_raw_value: float | None = None
    clean_values: list[float] = []     # rolling_mean 계산을 위해 최근 값들을 기억해둠

    while True:
        # XREAD: Stream에서 데이터를 읽어오는 명령어
        # block=5000: 새 데이터가 없으면 최대 5000ms(5초) 동안 기다림 (그동안 CPU를 계속 쓰지 않음)
        # count=10: 한 번에 최대 10개까지만 가져옴
        # Redis Client 자체는 동기(sync) 라이브러리라, asyncio 이벤트 루프를
        # 블로킹 하지 않도록 별도 스레드에서 실행 (to_thread)
        response = await asyncio.to_thread(
            redis_client.xread, {STREAM_NAME: last_id}, block=5000, count=10
        )

        if not response:
            continue

        # response 구조: [(스트림이름, [(entry_id, {필드: 값}), ...])]
        _, entries = response[0]

        for entry_id, fields in entries:
            value = float(fields["value"])
            features = build_features(value, last_raw_value, clean_values)

            try:
                result = await asyncio.to_thread(call_predict_api, features)

            except requests.exceptions.RequestException as e:
                # API 서버가 꺼져있거나 응답이 안 오는 경우, 여기서 전체가 죽지 않고 넘어가게 함
                print(f"[{entry_id}] 예측 API 호출 실패: {e}")
                last_id = entry_id
                last_raw_value = value
                continue

            now = datetime.now(timezone.utc).isoformat()

            # 프론트엔드로 보낼 메세지 구성
            message = {
                "timestamp": now,
                "value": value,
                "reconstruction_error": result["reconstructed_error"],
                "threshold": result["threshold"],
                "is_anomaly": result["is_anomaly"]
            }

            print(f"broadcast 예정: {message}")
            await manager.broadcast(message)

            last_id = entry_id
            last_raw_value = value

            # 정상으로 판정된 경우에만 깨끗한 기록에 추가
            if not result["is_anomaly"]:
                clean_values.append(value)

                if len(clean_values) > 200:
                    clean_values.pop(0)