interface StatusBadgeProps {
    isConnected: boolean;
    isAnomaly: boolean;
}

export function StatusBadge({ isConnected, isAnomaly }: StatusBadgeProps) {
    if (!isConnected) {
        return (
            <div style={{ padding: "8px 16px", borderRadius: 8, background: "#374151", color: "#9CA3AF" }}>
                연결 중..
            </div>
        );
    }

    return (
        <div
            style={{
                padding: "8px 16px",
                borderRadius: 8,
                background: isAnomaly ? "#7F1D1D" : "#064E3B",
                color: isAnomaly ? "#FCA5A5" : "#6EE7B7",
                fontWeight: 600,
            }}
        >
            {isAnomaly ? "🚨 이상치 감지됨" : "✅ 정상"}
        </div>
    );
}
