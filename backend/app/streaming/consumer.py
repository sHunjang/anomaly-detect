"""
Redis Stream에서 새로 들어온 데이터를 읽어와 처리하는 소비자(Consumer)
- 지금은 일단 "읽어서 출력"만 함. 다음 단계에서 여기에 /predict 로직을 연결할 예정
"""

import redis

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

STREAM_NAME = "sensor-stream"


def run_consumer():
    print(f"Consumer 시작 - '{STREAM_NAME}'을 계속 읽습니다. (Ctrl+C로 종료)")

    # "$"는 "지금 이 순간 이후에 새로 들어오는 것부터 읽겠다"라는 뜻
    # (스트림에 이미 쌓여있던 과거 데이터는 버리고, 새로 들어오는 것만 봄)
    last_id = "$"

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
            timestamp = fields["timestamp"]

            print(f"[{entry_id}] 수신: value={value}, timestamp={timestamp}")

            # 다음 번 XREAD 때는 "방금 처리한 것 다음부터" 읽어야 하므로 last_id 갱신
            last_id = entry_id


if __name__ == "__main__":
    run_consumer()