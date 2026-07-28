import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    // Scatter,
    // ScatterChart,
    Tooltip,
    XAxis,
    YAxis,
    // ZAxis,
} from "recharts";
import type { PredictionMessage } from "../types/prediction";

interface RealtimeChartProps {
    data: PredictionMessage[];
}

export function RealtimeChart({ data }: RealtimeChartProps) {
    // recharts가 다루기 쉽도록, 시간을 짧은 문자열로 변환하고 인덱스를 부여
    const chartData = data.map((d, index) => ({
        index,
        time: new Date(d.timestamp).toLocaleTimeString(),
        value: d.value,
        // 이상치인 경우에만 값을 넣고, 아니면 null -> recharts가 null은 점을 안 찍음
        anomalyValue: d.is_anomaly ? d.value : null,
    }));

    return (
        <div style={{ width: "100%", height: 300 }}>
            <ResponsiveContainer>
                <LineChart data={chartData}>
                    <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#374151"
                    />
                    <XAxis
                        dataKey="time"
                        tick={{ fontSize: 10, fill: "#9CA3AF" }}
                        minTickGap={40}
                    />
                    <YAxis tick={{ fill: "#9CA3AF" }} />
                    <Tooltip
                        contentStyle={{ background: "#1F2937", border: "none", borderRadius: 8 }}
                        labelStyle={{ color: "#9CA3AF" }}
                    />
                    {/* 전체 값의 흐름을 보여주는 기본 라인 */}
                    <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#60A5FA"
                        strokeWidth={1.5}
                        dot={false}
                    />
                    {/* 이상치인 지점만 빨간 점으로 덧그림 */}
                    <Line
                        type="monotone"
                        dataKey="anomalyValue"
                        stroke="none"
                        dot={{ r: 5, fill: "#EF4444" }}
                        isAnimationActive={false}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
