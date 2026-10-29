// GET /api/status — 공개용 서버 상태. Grafana Cloud Prometheus를 읽기 전용 토큰으로 대신 조회한다.
// 응답에는 공개 컨테이너 id(infra.json)와 상태, 호스트 % 숫자만 싣는다.
// cAdvisor 라벨·호스트 이름·IP·쿼리는 절대 내보내지 않는다.
// 환경 변수: GRAFANA_PROM_URL(…grafana.net/api/prom), GRAFANA_PROM_USER(인스턴스 id), GRAFANA_PROM_TOKEN(metrics:read)
import infra from "../../shared/infra.json";

const TTL = 60; // 초. 방문자 수와 상관없이 조회는 데이터센터당 1분에 한 번 정도로 묶인다.
const FAIL_TTL = 10; // 초. 조회 실패 응답은 짧게만 캐시해 곧 다시 시도한다.
const STALE = 180; // 초. 스크레이프 간격이 60초라 마지막 지표가 3분보다 오래되면 사라진 것으로 본다.
const RESTART_WINDOW = 600; // 초. 최근 10분 안에 (재)시작했으면 주의.
const MEM_WARN = 0.9; // 메모리 한도 대비 사용률. (container_oom_events_total은 이 서버에서 믿을 수 없어 쓰지 않는다)

// source(cAdvisor container 라벨) → 공개 id
const SOURCE_TO_ID = new Map(
  infra.units.flatMap((u) => (u.containers ?? []).map((c) => [c.source, c.id])),
);

const CAD = 'job="integrations/cadvisor",container!=""';
const UNIX = 'job="integrations/unix"';
const tag = (q, expr) => `label_replace(${expr}, "q", "${q}", "", "")`;
// 한 번의 요청으로 모든 신호를 받는다. 결과 시리즈마다 q 라벨로 신호를 구분한다.
const QUERY = [
  tag("seen", `time() - max by (container) (timestamp(container_last_seen{${CAD}}))`),
  tag("uptime", `time() - max by (container) (container_start_time_seconds{${CAD}})`),
  tag("mem", `max by (container) (container_memory_working_set_bytes{${CAD}}) / max by (container) (container_spec_memory_limit_bytes{${CAD}} > 0)`),
  tag("health", `max by (container) (max_over_time(container_health_state{${CAD}}[3m]))`),
  tag("host_seen", `time() - max(timestamp(node_memory_MemTotal_bytes{${UNIX}}))`),
  tag("cpu", `100 * (1 - avg(rate(node_cpu_seconds_total{${UNIX},mode="idle"}[5m])))`),
  tag("host_mem", `100 * (1 - max(node_memory_MemAvailable_bytes{${UNIX}}) / max(node_memory_MemTotal_bytes{${UNIX}}))`),
  tag("disk", `100 * (1 - max(node_filesystem_avail_bytes{${UNIX},mountpoint="/"}) / max(node_filesystem_size_bytes{${UNIX},mountpoint="/"}))`),
].join(" or ");

let memo = null; // { at, ttl, body } — 같은 isolate 안의 요청은 Cache API 없이도 묶는다.

export async function onRequestGet({ request, env, waitUntil }) {
  if (memo && Date.now() - memo.at < memo.ttl * 1000) return reply(memo.body, memo.ttl);

  const cache = caches.default;
  const key = new Request(new URL("/api/status", request.url).toString());
  const hit = await cache.match(key);
  if (hit) return hit;

  const status = await buildStatus(env);
  const ttl = Object.keys(status.containers).length ? TTL : FAIL_TTL;
  const body = JSON.stringify(status);
  memo = { at: Date.now(), ttl, body };
  const res = reply(body, ttl);
  waitUntil(cache.put(key, res.clone()));
  return res;
}

function reply(body, ttl) {
  return new Response(body, {
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": `public, max-age=${ttl}`,
    },
  });
}

async function buildStatus(env) {
  const updatedAt = new Date().toISOString();
  let series;
  try {
    series = await queryProm(env, QUERY).catch(() => queryProm(env, QUERY)); // 한 번 더 시도
  } catch (e) {
    console.error("status query failed:", e.message); // Pages 로그에만 남는다.
    // 조회 실패: 모든 컨테이너를 "데이터 없음"으로 둔다.
    return { updatedAt, containers: {}, host: {} };
  }

  const host = {};
  let hostSeen = Infinity;
  const signals = new Map(); // source → { seen, uptime, mem, health }
  for (const { metric, value } of series) {
    const v = Number(value[1]);
    if (!Number.isFinite(v)) continue;
    if (metric.container) {
      if (!signals.has(metric.container)) signals.set(metric.container, {});
      signals.get(metric.container)[metric.q] = v;
    } else if (metric.q === "host_seen") hostSeen = v;
    else if (metric.q === "cpu") host.cpu = round(v);
    else if (metric.q === "host_mem") host.mem = round(v);
    else if (metric.q === "disk") host.disk = round(v);
  }

  // 호스트 지표가 없으면 서버 전체를 알 수 없다: 컨테이너를 error로 단정하지 않고 비운다.
  if (hostSeen > STALE) return { updatedAt, containers: {}, host: {} };

  const containers = {};
  for (const [source, id] of SOURCE_TO_ID) {
    containers[id] = judge(signals.get(source));
  }
  return { updatedAt, containers, host };
}

// 호스트는 살아 있다는 전제에서 컨테이너 하나의 상태.
function judge(s) {
  if (!s || !(s.seen <= STALE)) return "error"; // 지표가 사라졌다 = 컨테이너가 없다
  if (s.health === 0) return "error"; // 3분 내내 healthcheck 실패
  if (s.uptime < RESTART_WINDOW) return "warn";
  if (s.mem >= MEM_WARN) return "warn";
  return "ok";
}

async function queryProm(env, query) {
  const url = `${env.GRAFANA_PROM_URL.replace(/\/$/, "")}/api/v1/query`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      authorization: `Basic ${btoa(`${env.GRAFANA_PROM_USER}:${env.GRAFANA_PROM_TOKEN}`)}`,
      "content-type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({ query }),
    signal: AbortSignal.timeout(8000),
  });
  if (!res.ok) throw new Error(`prom ${res.status}`);
  const json = await res.json();
  if (json.status !== "success") throw new Error("prom error");
  return json.data.result;
}

const round = (v) => Math.round(v * 10) / 10;
