// 상태 API들이 함께 쓰는 Grafana Cloud Prometheus 조회. 라우트가 아니다(onRequest 없음).
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

export const round = (v) => Math.round(v * 10) / 10;
