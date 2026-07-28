"""
Redis Stream에서 새로 들어온 데이터를 읽어와, FastAPI의 /predict에 요청을 보내
실시간으로 이상치 여부를 판정하는 소비자(Consumer)
"""

from datetime import datetime, timezone

import redis
import requests

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

STREAM_NAME = "sensor-stream"
PREDICT_URL = "http://localhost:8000/predict"


def build_features(value: float, recent_values: list[float]) -> dict:
    """
    trian_autoencoder.py에서 썼던 feature 4개를 실시간 데이터 기준으로 계산
    
    - recent_values: 최근 들어온 값들의 기록 (rolling mean 계산에 필요)
    """

    if len(recent_values) == 0:
        value_diff = 0.0
    else:
        value_diff = value - recent_values[-1]

    # 최근 30개, 200개 평균 (데이터가 그만큼 안 쌓였으면 있는 만큼만 사용)
    window_30 = recent_values[-30:] + [value]
    window_200 = recent_values[-200:] + [value]

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


def run_consumer():
    print(f"Consumer 시작 - '{STREAM_NAME}'을 계속 읽고, {PREDICT_URL}로 판정 요청을 보냄...")

    # "$"는 "지금 이 순간 이후에 새로 들어오는 것부터 읽겠다"라는 뜻
    # (스트림에 이미 쌓여있던 과거 데이터는 버리고, 새로 들어오는 것만 봄)
    last_id = "$"
    recent_values: list[float] = []     # rolling_mean 계산을 위해 최근 값들을 기억해둠

    while True:
        # XREAD: Stream에서 데이터를 읽어오는 명령어
        # block=5000: 새 데이터가 없으면 최대 5000ms(5초) 동안 기다림 (그동안 CPU를 계속 쓰지 않음)
        # count=10: 한 번에 최대 10개까지만 가져옴
        response = redis_client.xread({STREAM_NAME: last_id}, block=5000, count=10)

        if not response:
            # 5초 동안 새 데이터가 없었다는 뜻. 그냥 다시 대기하러 감
            print("... 새 데이터 대기 중 ...")
            continue

        # response 구조: [(스트림이름, [(entry_id, {필드: 값}), ...])]
        _, entries = response[0]

        for entry_id, fields in entries:
            value = float(fields["value"])

            features = build_features(value, recent_values)

            try:
                result = call_predict_api(features)

            except requests.exceptions.RequestException as e:
                # API 서버가 꺼져있거나 응답이 안 오는 경우, 여기서 전체가 죽지 않고 넘어가게 함
                print(f"[{entry_id}] 예측 API 호출 실패: {e}")

                last_id = entry_id
                recent_values.append(value)
                continue

            status = "🚨 이상치!" if result["is_anomaly"] else "정상"
            now = datetime.now(timezone.utc).strftime("%H:%M:%S")

            print(
                f"[{now}] value={value:.2f} | error={result['reconstructed_error']:.4f} "
                f"| threshold={result['threshold']:.4f} | {status}"
            )

            last_id = entry_id
            recent_values.append(value)

            # 메모리가 무한정 커지지 않도록 최근 200개까지만 유지
            if len(recent_values) > 200:
                recent_values.pop(0)


if __name__ == "__main__":
    run_consumer()