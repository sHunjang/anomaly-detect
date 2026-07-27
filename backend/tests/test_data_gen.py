"""data_gen.py가 예상한 형태의 데이터를 만드는지 검증하는 테스트"""

import sys
from pathlib import Path

# ml 폴더의 모듈을 import 하기 위해 경로 추가
sys.path.append(str(Path(__file__).parent.parent / "ml"))

from data_gen import generate_dataset


def test_generate_dataset_has_expected_columns():
    """생성된 데이터프레임에 필요한 컬럼이 다 있는지 확인"""
    df = generate_dataset(n_points=100)  # 테스트는 빠르게 돌아야 하니 작은 크기로
    expected_columns = {"timestamp", "value", "baseline", "is_anomaly", "anomaly_type"}
    assert expected_columns.issubset(df.columns)


def test_generate_dataset_has_correct_length():
    """요청한 개수만큼 데이터가 생성되는지 확인"""
    df = generate_dataset(n_points=100)
    assert len(df) == 100


def test_anomaly_labels_are_binary():
    """is_anomaly 컬럼이 0 또는 1로만 이루어져 있는지 확인"""
    df = generate_dataset(n_points=100)
    assert set(df["is_anomaly"].unique()).issubset({0, 1})