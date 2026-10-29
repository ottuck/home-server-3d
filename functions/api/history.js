// GET /api/history — 벽 모니터용 최근 1시간 호스트 지표(1분 간격). 서버 전체 합계 숫자만 싣는다.
import { UNIX, cachedJson, prom, round, tag } from "../_lib/prom.js";

const TTL = 60; // 초. 캐시 기간
const FAIL_TTL = 10;
const SPAN = 3600; // 초. 보여 줄 기간
const STEP = 60; // 초. 스크레이프 간격과 같다
const NIC = `${UNIX},device!~"lo|tailscale.*|veth.*|docker.*|br-.*"`; // 바깥과 주고받는 인터페이스만

const QUERY = [
  tag("cpu", `100 * (1 - avg(rate(node_cpu_seconds_total{${UNIX},mode="idle"}[3m])))`),
  tag("mem", `100 * (1 - max(node_memory_MemAvailable_bytes{${UNIX}}) / max(node_memory_MemTotal_bytes{${UNIX}}))`),
  tag("disk", `100 * (1 - max(node_filesystem_avail_bytes{${UNIX},mountpoint="/"}) / max(node_filesystem_size_bytes{${UNIX},mountpoint="/"}))`),
  tag("netIn", `sum(rate(node_network_receive_bytes_total{${NIC}}[3m]))`),
  tag("netOut", `sum(rate(node_network_transmit_bytes_total{${NIC}}[3m]))`),
].join(" or ");
const NAMES = ["cpu", "mem", "disk", "netIn", "netOut"];

// 응답: { updatedAt, start, step, series: { cpu, mem, disk: [%], netIn, netOut: [바이트/초] } }
// 배열 길이는 SPAN/STEP + 1이고, 값이 없는 칸은 null이다. 조회 실패면 series가 {}다.
export const onRequestGet = cachedJson("/api/history", async (env) => {
  const end = Math.floor(Date.now() / 1000 / STEP) * STEP;
  const start = end - SPAN;
  const data = { updatedAt: new Date().toISOString(), start: new Date(start * 1000).toISOString(), step: STEP, series: {} };
  let result;
  try {
    result = await prom(env, "query_range", { query: QUERY, start, end, step: STEP });
  } catch (e) {
    console.error("history query failed:", e.message);
    return { data, ttl: FAIL_TTL };
  }
  for (const { metric, values } of result) {
    if (!NAMES.includes(metric.q)) continue;
    const list = new Array(SPAN / STEP + 1).fill(null);
    for (const [t, v] of values) {
      const i = Math.round((t - start) / STEP);
      const n = Number(v);
      if (i >= 0 && i < list.length && Number.isFinite(n)) list[i] = metric.q.startsWith("net") ? Math.round(n) : round(n);
    }
    data.series[metric.q] = list;
  }
  return { data, ttl: TTL };
});
