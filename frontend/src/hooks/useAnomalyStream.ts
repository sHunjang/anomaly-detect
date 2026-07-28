import { useEffect, useRef, useState } from "react";
import type { PredictionMessage } from "../types/prediction";

const WS_URL = "ws://localhost:8000/ws/stream";
const MAX_POINTS = 100; // 차트에 너무 많은 점이 쌓이지 않도록 최근 100개만 유지

interface UseAnomalyStreamResult {
    data: PredictionMessage[];
    isConnected: boolean;
    latestAnomaly: PredictionMessage | null;
}

export function useAnomalyStream(): UseAnomalyStreamResult {
    const [data, setData] = useState<PredictionMessage[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [latestAnomaly, setLatestAnomaly] = useState<PredictionMessage | null>(null);

    // useRef: 리렌더링 사이에도 값이 유지되지만, 값이 바뀌어도 화면을 다시 그리진 않음
    // WebSocket 객체 자체는 화면에 보여줄 게 아니라 "연결을 유지하는 용도"라 ref가 적합
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log("WebSocket 연결됨");
            setIsConnected(true);
        };

        ws.onmessage = (event) => {
            console.log("받은 원본 데이터:", event.data);
            const message: PredictionMessage = JSON.parse(event.data);

            setData((prev) => {
                const next = [...prev, message];

                // 100개 넘으면 오래된 것부터 제거 (메모리와 차트 가독성 관리)
                return next.length > MAX_POINTS ? next.slice(next.length - MAX_POINTS) : next;
            });

            if (message.is_anomaly) {
                setLatestAnomaly(message);
            }
        };

        ws.onclose = () => {
            console.log("WebSocket 연결 종료됨");
            setIsConnected(false);
        };

        ws.onerror = (error) => {
            console.error("WebSocket 에러: ", error);
        };

        // 컴포넌트가 사라질 때(cleanup) 연결도 같이 정리
        // 이게 없으면 페이지를 여러 번 새로고침 할 때마다 연결이 계속 쌓이는 누수가 생김
        return () => {
            ws.close();
        };
    }, []); // 빈 배열: 컴포넌트가 처음 마운트될 때 딱 합 번만 연결

    return { data, isConnected, latestAnomaly };
}
