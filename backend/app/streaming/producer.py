"""
Redis Stream에 가짜 센서 데이터를 계속 흘려보내는 생산자(Producer)
- 실제 서비스라면 진짜 센서/로그 시스템이 이 역할을 하지만,
    여기서는 data_gen.py 로직을 재활용해서 실시간처럼 흉내냄
"""

import time
from datetime import datetime, timezone

import numpy as np
import redis

# Redis 서버에 연결
# host="localhost": 로컬환경에서 동작하고 있는 Redis에 접속
# port=6379: Redis 기본 포트 (brew services start redis로 이미 떠있음)
# decode_response=True: Redis가 돌려주는 값을 바이트(b'...')가 아니라 일반 문자열로 받게 함
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

STREAM_NAME = "sensor-stream"


def generate_next_value(t: int) -> float:
    """
    간단한 sin 파형 + 노이즈로 다음 값을 하나 생성
    가끔(5% 확률) 스파이크를 섞어서 이상치도 발생
    """

    base = 100 + 15 * np.sin(2 * np.pi * t / 1440)
    noise = np.random.normal(0, 2)
    value = base + noise

    if np.random.random() < 0.05:   # 5% 확률로 스파이크 발생
        value += np.random.uniform(3, 5)

    return round(value, 2)


def run_producer():
    print(f"Producer 시작 - '{STREAM_NAME}'에 데이터를 계속 보냄. (Ctrl+C로 종료)")

    t = 0

    while True:
        value = generate_next_value(t)

        # XADD: Redis Stream에 새 항목을 추가하는 명령어
        # "*"는 "ID를 Redis가 알아서 자동으로(현재 시각 기준) 붙여줘)"라는 뜻
        # 두 번째 인자는 실제로 저장할 데이터 (딕셔너리 형태, 문자열이어야 함)
        entry_id = redis_client.xadd(
            STREAM_NAME,
            {
                "value": str(value),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        print(f"[{entry_id}] 전송: value={value}")

        t += 1
        time.sleep(1)   # 1초마다 하나씩 (실제로는 훨씬 빠를 수 있지만, 눈으로 확인할 수 있도록 느리게)


if __name__ == "__main__":
    run_producer()