// API들이 함께 쓰는 응답 캐시. 라우트가 아니다(onRequest 없음).

// build(env) → { data, ttl }. 결과를 ttl초 동안 isolate 메모리와 Cache API에 둔다.
// 방문자 수와 상관없이 바깥 조회(Grafana, GitHub)는 데이터센터당 ttl마다 한 번 정도로 묶인다.
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
