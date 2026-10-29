// 상태 API들이 함께 쓰는 Grafana Cloud Prometheus 조회와 캐시. 라우트가 아니다(onRequest 없음).
// 환경 변수: GRAFANA_PROM_URL(…grafana.net/api/prom), GRAFANA_PROM_USER(인스턴스 id), GRAFANA_PROM_TOKEN(metrics:read)

export const CAD = 'job="integrations/cadvisor",container!=""';
export const UNIX = 'job="integrations/unix"';
// 쿼리 여러 개를 `or`로 묶어 한 번에 받을 때, 결과 시리즈마다 q 라벨로 신호를 구분한다.
export const tag = (q, expr) => `label_replace(${expr}, "q", "${q}", "", "")`;

// path: "query" 또는 "query_range". 실패하면 한 번 더 시도한다.
export async function prom(env, path, params) {
  const once = async () => {
    const res = await fetch(`${env.GRAFANA_PROM_URL.replace(/\/$/, "")}/api/v1/${path}`, {
      method: "POST",
      headers: {
        authorization: `Basic ${btoa(`${env.GRAFANA_PROM_USER}:${env.GRAFANA_PROM_TOKEN}`)}`,
        "content-type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams(params),
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) throw new Error(`prom ${res.status}`);
    const json = await res.json();
    if (json.status !== "success") throw new Error("prom error");
    return json.data.result;
  };
  return once().catch(once);
}

// build(env) → { data, ttl }. 결과를 ttl초 동안 isolate 메모리와 Cache API에 둔다.
// 방문자 수와 상관없이 Grafana 조회는 데이터센터당 ttl마다 한 번 정도로 묶인다.
export function cachedJson(path, build) {
  let memo = null; // { at, ttl, body }
  return async ({ request, env, waitUntil }) => {
    if (memo && Date.now() - memo.at < memo.ttl * 1000) return reply(memo.body, memo.ttl);
    const key = new Request(new URL(path, request.url).toString());
    const hit = await caches.default.match(key);
    if (hit) return hit;

    const { data, ttl } = await build(env);
    const body = JSON.stringify(data);
    memo = { at: Date.now(), ttl, body };
    const res = reply(body, ttl);
    waitUntil(caches.default.put(key, res.clone()));
    return res;
  };
}

function reply(body, ttl) {
  return new Response(body, {
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": `public, max-age=${ttl}`,
    },
  });
}

export const round = (v) => Math.round(v * 10) / 10;
