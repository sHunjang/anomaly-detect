# Anomaly Detection Dashboard

시계열 데이터의 이상치(스파이크/드리프트/레벨시프트)를 실시간으로 탐지하고 시각화하는 프로젝트입니다.

## 개요

- 합성 시계열 데이터를 생성하고, 두 가지 비지도학습 모델(Isolation Forest, Autoencoder)로 이상치 탐지 성능을 비교
- 학습된 모델을 API로 서빙하고, Redis Streams 기반 실시간 파이프라인을 구축
- WebSocket으로 프론트엔드에 실시간 판정 결과를 전달하는 대시보드 구현

## 기술 스택

**Backend**

- Python 3.10, FastAPI
- PyTorch (Autoencoder, MPS 가속), scikit-learn (Isolation Forest)
- Redis Streams (실시간 데이터 파이프라인)
- PostgreSQL (예정 / 미사용 시 제거)

**Frontend**

- React + TypeScript (Vite)
- Recharts (실시간 차트)
- WebSocket

**인프라 / 형상관리**

- Docker (Redis, PostgreSQL 로컬 실행)
- Git Flow (main / develop / feature / release)
- GitHub Actions (CI: ruff lint, pytest)
- pre-commit (ruff 자동 검사)

## 아키텍처

```bash
[Producer: 가짜 센서 데이터 생성]

↓ (Redis Stream)

[FastAPI 백그라운드 Consumer]
```

- Redis에서 데이터 읽기
- feature 계산 (rolling mean, deviation 등)
- /predict 호출 → Autoencoder 추론
  ↓ (WebSocket broadcast)
  [React 대시보드]
- 실시간 라인 차트
- 이상치 발생 이력

## 모델 비교 결과

| 이상치 타입 | Isolation Forest | Autoencoder |
| ----------- | ---------------- | ----------- |
| Spike       | 100%             | 100%        |
| Level Shift | 52.9%            | 80%         |
| Drift       | 28.9%            | 50%         |

Autoencoder가 전반적으로 우수했으며, 특히 서서히 변하는 패턴(drift, level shift)에서 격차가 두드러짐.

## 실행 방법

### 1. 환경 설정

```bash
conda create -n anomaly-detect python=3.10 -y
conda activate anomaly-detect
cd backend
pip install -r requirements.txt
```

### 2. Redis 실행

```bash
brew services start redis
```

### 3. 모델 학습 및 저장

```bash
python ml/save_model.py
```

### 4. 백엔드 서버 실행

```bash
uvicorn app.main:app --reload
```

### 5. 데이터 생산자 실행 (별도 터미널)

```bash
python app/streaming/producer.py
```

### 6. 프론트엔드 실행 (별도 터미널)

```bash
cd frontend
npm install
npm run dev
```

`http://localhost:5173`에서 대시보드 확인 가능.

## 프로젝트 구조

```bash
anomaly-detect/
├── backend/
│ ├── app/
│ │ ├── api/ # REST 라우터 (/predict)
│ │ ├── models/ # Pydantic 스키마, 추론 서비스
│ │ ├── streaming/ # Redis Streams producer/consumer, WebSocket manager
│ │ └── main.py
│ ├── ml/ # 데이터 생성, 모델 학습, 저장/불러오기
│ └── tests/
└── frontend/
└── src/
├── api/
├── components/
├── hooks/
└── types/
```

## 학습 목표 및 배운 것

- 비지도학습 기반 이상탐지 (Isolation Forest, Autoencoder) 원리와 한계
- feature engineering이 모델 성능에 미치는 영향
- 실시간 스트리밍 파이프라인 설계 (Redis Streams, WebSocket)
- Git Flow 기반 형상관리, CI/CD, pre-commit을 통한 코드 품질 관리

## 향후 개선 가능 사항

- Slack/Discord를 통한 이상치 알림
- 학습/검증 데이터 분리를 통한 오버피팅 검증
- Docker Compose로 전체 스택 통합 실행
