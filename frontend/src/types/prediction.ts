/**
 * 백엔드 consumer.py의 broadcast 메세지 형식과 정확히 맞춰야 함
 * 여기 필드명이 백엔드와 하나라도 다르면, 데이터는 오는데 화면엔 undefined로 뜨는 버그 발생
 */

export interface PredictionMessage {
    timestamp: string;
    value: number;
    reconstruction_error: number;
    threshold: number;
    is_anomaly: boolean;
}
