import type { PredictionMessage } from "../types/prediction";

interface AlertLogProps {
    data: PredictionMessage[];
}

export function AlertLog({ data }: AlertLogProps) {
    // 전체 데이터 중 이상치인 것만 골라서, 최신 순으로 정렬
    const anomalies = data
        .filter((d) => d.is_anomaly)
        .slice()
        .reverse();

    return (
        <div>
            <h3 style={{ color: "#E5E7EB", fontSize: 14, marginBottom: 8 }}>이상치 발생 이력 ({anomalies.length}건)</h3>
            <div style={{ maxHeight: 200, overflowY: "auto" }}>
                {anomalies.length === 0 && (
                    <p style={{ color: "#6B7280", fontSize: 13 }}>아직 감지된 이상치가 없습니다.</p>
                )}
                {anomalies.map((a) => (
                    <div
                        key={a.timestamp}
                        style={{
                            display: "flex",
                            justifyContent: "space-between",
                            padding: "6px 10px",
                            borderBottom: "1px solid #374151",
                            fontSize: 13,
                            color: "#FCA5A5",
                        }}
                    >
                        <span>{new Date(a.timestamp).toLocaleTimeString()}</span>
                        <span>value: {a.value.toFixed(2)}</span>
                        <span>error: {a.reconstruction_error.toFixed(3)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
