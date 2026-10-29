// 컨테이너 상태. 지금은 가짜 데이터, Phase 4에서 Worker 응답으로 바꾼다.

// blender/rack.py STATUS_COLOR와 같은 값(선형 RGB).
export const STATUS_COLOR = {
  ok: [0.25, 1.0, 0.45],
  warn: [1.0, 0.62, 0.12],
  error: [1.0, 0.16, 0.12],
  unknown: [0.45, 0.47, 0.5],
};

// 반환 형태: { updatedAt: ISO 문자열, containers: { [cAdvisor container 라벨]: "ok" | "warn" | "error" } }
// 여기에 없는 컨테이너는 "unknown"으로 칠한다. 데이터가 없으면 절대 정상으로 칠하지 않는다.
export async function fetchStatus(infra) {
  // Phase 4: return (await fetch("/api/status")).json();
  return fakeStatus(infra);
}

let tick = 0;
function fakeStatus(infra) {
  const names = infra.units.flatMap((u) => u.containers ?? []);
  const containers = {};
  names.forEach((name, i) => {
    // 대부분 정상, 몇 개는 돌아가며 주의·오류, 하나는 데이터 없음(키 생략).
    const r = (i * 7 + tick * 3) % names.length;
    if (r === 0) return;
    containers[name] = r === 1 ? "error" : r === 2 || r === 5 ? "warn" : "ok";
  });
  tick++;
  return { updatedAt: new Date().toISOString(), containers };
}

export function containerStatus(status, name) {
  return status?.containers?.[name] ?? "unknown";
}

// 유닛 상태 = 컨테이너 중 가장 나쁜 상태. 컨테이너가 없는 유닛은 null.
export function unitStatus(status, unit) {
  const list = (unit.containers ?? []).map((c) => containerStatus(status, c));
  if (!list.length) return null;
  if (list.includes("error")) return "error";
  if (list.includes("warn")) return "warn";
  if (list.includes("unknown")) return "unknown";
  return "ok";
}
