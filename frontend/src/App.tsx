import { useAnomalyStream } from "./hooks/useAnomalyStream";
import { StatusBadge } from "./components/StatusBadge";
import { RealtimeChart } from "./components/RealtimeChart";
import { AlertLog } from "./components/AlertLog";

function App() {
    const { data, isConnected, latestAnomaly } = useAnomalyStream();

    // 가장 최근 데이터가 이상치였는지 (없으면 false)
    const currentIsAnomaly = data.length > 0 && data[data.length - 1].is_anomaly;

    return (
        <div style={{ background: "#111827", minHeight: "100vh", padding: 24, fontFamily: "sans-serif" }}>
            <div style={{ maxWidth: 900, margin: "0 auto" }}>
                <div
                    style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}
                >
                    <h1 style={{ color: "#F9FAFB", fontSize: 20 }}>실시간 이상탐지 대시보드</h1>
                    <StatusBadge
                        isConnected={isConnected}
                        isAnomaly={currentIsAnomaly}
                    />
                </div>

                <div style={{ background: "#1F2937", borderRadius: 12, padding: 20, marginBottom: 20 }}>
                    <RealtimeChart data={data} />
                </div>

                <div style={{ background: "#1F2937", borderRadius: 12, padding: 20 }}>
                    <AlertLog data={data} />
                </div>

                {latestAnomaly && (
                    <p style={{ color: "#6B7280", fontSize: 12, marginTop: 12 }}>
                        최근 이상치: {new Date(latestAnomaly.timestamp).toLocaleTimeString()}
                    </p>
                )}
            </div>
        </div>
    );
}

export default App;
