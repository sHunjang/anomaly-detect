"""
Isolation Forest로 이상탐지 모델 학습 + 평가
- data_gen.py로 만든 synthetic_timeseries.csv를 불러와서 학습
- 이미 정답(is_anomaly)을 알고 있으니, 모델이 얼마나 잘 맞췄는지도 채점
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix


DATA_PATH = Path(__file__).parent / "data" / "synthetic_timeseries.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    return df


def build_feature(df: pd.DataFrame) -> np.ndarray:
    """
    Isolation Forest에 넣을 입력값(feature)을 준비

    - value_diff: 직전 값과의 차이 -> 스파이크처럼 순간적으로 튀는 패턴 감지용
    - deviation_from_trend: 최근 30분 평균 대비 현재 값의 차이 -> drift처럼 서서히 흐름에서 
        벗어나는 패턴을 감지하기 위해 추가
    - short_vs_long_trend: 단기 흐름(30분) vs 장기 흐름(200분)의 차이 -> drift 감지용
        drift는 단기 평균도 같이 끌려 올라가서 deviation_from_trend만으로는 안 잡히니,
        "천천히 움직이는 장기 기준선"과 비교해서 그 차이를 비교
    """

    df = df.copy()

    # diff(): 바로 이전 시점과의 차이. 첫 값은 비교 대상이 없어서 NaN이 되므로 0으로 채움
    df["value_diff"] = df["value"].diff().fillna(0)

    # rolling(window=30): 현재 시점 기준 직전 30개(30분치) 값의 평균을 구함
    # min_periods=1: 데이터 시작 부분(30개가 안 모인 초반)도 있는 만큼만 평균내서 NaN 방지
    df["rolling_mean_30"] = df["value"].rolling(window=30, min_periods=1).mean()

    # "지금 값이 최근 흐름(추세)에서 얼마나 벗어났는지" -> drift 탐지의 핵심 feature
    df["deviation_from_trend"] = df["value"] - df["rolling_mean_30"]

    # 200분 (약 3시간 20분) 평균 - 장기 기준선
    df["rolling_mean_200"] = df["value"].rolling(window=200, min_periods=1).mean()

    # 단기 평균과 장기 평균의 차이 -> drift처럼 서서히 벌어지는 흐름을 잡기 위한 feature
    df["short_vs_long_trend"] = df["rolling_mean_30"] - df["rolling_mean_200"]

    # feature 4개짜리 배열로 확장 (기존 3개 -> 4개)
    features = df[["value", "value_diff", "deviation_from_trend", "short_vs_long_trend"]].values

    return features


def train_isolation_forest(X: np.ndarray) -> IsolationForest:
    """
    IsolationForest 모델 생성 및 학습

    Parameters:
        - n_estimators: 나무(tree)를 몇 개 만들지. 많을수록 안정적이지만 느려짐 (기본 100이면 충분)
        - contamination: 전체 데이터 중 "이상치일 것으로 예상되는 비율"
            이미 data_gen.py에서 대략 몇 %를 이상치로 넣었는지 알고 있으니 그 값을 참고해서 설정
            (모른다면 보통 'auto' 또는 0.01 ~ 0.05 정도로 시작)
        - random_state: 랜덤 시드 고정. 매번 같은 겨로가가 나오게 해서 재현 가능하게 함
    """

    model = IsolationForest(
        n_estimators=100,
        contamination=0.44,  # 실제 이상치 비율에 맞춤
        random_state=42,
    )

    # 지도학습이 아니라서 정답 라벨(y) 없이 X만 넣음.
    # 모델이 "어떤게 이상치인지" 배우는게 아리나, "데이터가 어떻게 흩어져 있는지" 스스로 파악
    model.fit(X)

    return model


def evaluate(df: pd.DataFrame, model: IsolationForest, X: np.ndarray):
    """
    모델의 예측 결과를 실제 정답(is_anomaly)과 비교해서 얼마나 잘 맞췄는지 확인
    """

    # predict() == 각 데이터가 정상인지 이상치인지 알려줌
    # sklearn 관례상 이상치는 -1, 정상은 1로 반환됨 (0/1이 아니라서 헷갈리기 쉬움)
    raw_predictions = model.predict(X)

    # 생성한 라벨(is_anomaly: 1=이상치, 0=정상)과 비교하기 쉽게 형식을 맞춰줌
    # -1(이상치) -> 1로, 1(정상) -> 0 으로 변환
    predict_anomaly = np.where(raw_predictions == -1, 1, 0)

    # decision_function(): 각 데이터가 "얼마나 이상한지" 점수로 알려줌
    # 점수가 낮을수록(음수에 가까울수록) 더 이상치에 가까움
    anomaly_scores = model.decision_function(X)

    df["predicted_anomaly"] = predict_anomaly
    df["anomaly_score"] = anomaly_scores

    print("=== 혼동 행렬 (Confusion Matrix) ===")
    # 행: 실제 정답, 열: 모델 예측, 대각선(왼쪽위, 오른쪽아래)이 맞춘 개수
    print(confusion_matrix(df["is_anomaly"], df["predicted_anomaly"]))

    print("\n=== 상세 리포트 ===")
    # precision(정밀도): 모델이 "이상하다"라고 한 것 중 진짜 이상치였던 비율
    # recall(재현율): 진짜 이상치들 중 모델이 실제로 찾아낸 비율
    print(classification_report(df["is_anomaly"], df["predicted_anomaly"], target_names=["noramal", "anomaly"]))

    # 이상치 타입별로 얼마나 잘 잡았는지도 따로 확인 (spike/drift/level_shift 중 뭘 못 잡는지 보려고)
    print("\n=== 이상치 타입별 탐지율 ===")
    for anomaly_type in ["spike", "drift", "level_shift"]:
        subset = df[df["anomaly_type"] == anomaly_type]

        if len(subset) == 0:
            continue

        detected_ratio = subset["predicted_anomaly"].mean()

        print(f"{anomaly_type}: {detected_ratio:.1%} 탐지됨 (총 {len(subset)} 개 중)")

    return df


if __name__ == "__main__":

    df = load_data()
    X = build_feature(df)

    model = train_isolation_forest(X)
    result_df = evaluate(df, model, X)

    # 나중에 시각화하거나 다른 모델(Autoencoder)과 비교할 수 있게 결과를 저장해둠
    output_path = Path(__file__).parent / "data" / "isolation_forest_result.csv"
    result_df.to_csv(output_path, index=False)

    print(f"\n 결과 저장 완료: {output_path}")