// 컨테이너 상태. /api/status(functions/api/status.js) 응답을 쓰고, 주소에 ?demo=1이 있으면 가짜 데이터를 쓴다.

// blender/rack.py STATUS_COLOR와 같은 값(선형 RGB).
export const STATUS_COLOR = {
  ok: [0.25, 1.0, 0.45],
  warn: [1.0, 0.62, 0.12],
  error: [1.0, 0.16, 0.12],
  unknown: [0.45, 0.47, 0.5],
};

// 반환 형태: { updatedAt: ISO 문자열, containers: { [컨테이너 공개 id(infra.json)]: "ok" | "warn" | "error" },
//            host: { cpu?, mem?, disk? } (% 숫자, 모르는 값은 키 없음) }
// 여기에 없는 컨테이너는 "unknown"으로 칠한다. 데이터가 없으면 절대 정상으로 칠하지 않는다.
// 가짜 상태에는 demo: true가 붙는다(패널이 "예시 데이터"로 표시). 실제 응답에는 없다.
// ?demo=1이거나, 로컬 정적 서버라 /api/status가 없으면(함수 없이 띄운 경우) 가짜 상태를 쓴다.
const DEMO = new URLSearchParams(location.search).has("demo");
const LOCAL = ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname);

export async function fetchStatus(infra) {
  if (DEMO) return fakeStatus(infra);
  try {
    const res = await fetch("/api/status");
    if (!res.ok) throw new Error(`status ${res.status}`);
    const s = await res.json();
    return { updatedAt: s.updatedAt, containers: s.containers ?? {}, host: s.host ?? {} };
  } catch {
    if (LOCAL) return fakeStatus(infra);
    return { updatedAt: new Date().toISOString(), containers: {}, host: {} };
  }
}

// 벽 모니터용 최근 1시간 호스트 지표(/api/history, functions/api/history.js).
// 반환 형태: { updatedAt, start: ISO, step: 초, series: { cpu, mem, disk: [%], netIn, netOut: [바이트/초] } }, 빈 칸은 null.
// 실패하면 series가 {}다. 가짜 기록에는 demo: true가 붙는다.
export async function fetchHistory() {
  if (DEMO) return fakeHistory();
  try {
    const res = await fetch("/api/history");
    if (!res.ok) throw new Error(`history ${res.status}`);
    const h = await res.json();
    return { updatedAt: h.updatedAt, start: h.start, step: h.step, series: h.series ?? {} };
  } catch {
    if (LOCAL) return fakeHistory();
    return { updatedAt: new Date().toISOString(), start: null, step: 60, series: {} };
  }
}

function fakeHistory() {
  const n = 61;
  const wave = (base, amp, f, k = 1) => Array.from({ length: n }, (_, i) =>
    Math.round((base + amp * Math.sin(i / f) + amp * 0.4 * Math.sin(i / 2.3 + f)) * k) / k);
  const start = new Date(Math.floor(Date.now() / 60000) * 60000 - (n - 1) * 60000).toISOString();
  return {
    updatedAt: new Date().toISOString(), demo: true, start, step: 60,
    series: { cpu: wave(9, 4, 5, 10), mem: wave(66, 2, 9, 10), disk: wave(23.4, 0.05, 20, 10), netIn: wave(2400, 600, 4), netOut: wave(1900, 500, 6) },
  };
}

// 책상 모니터용 공개 저장소 최근 커밋(/api/github, functions/api/github.js).
// 반환 형태: { updatedAt, user, commits: [{ repo, sha, message, date }] }. 실패하면 commits가 빈 배열이다.
export async function fetchGithub() {
  if (DEMO) return fakeGithub();
  try {
    const res = await fetch("/api/github");
    if (!res.ok) throw new Error(`github ${res.status}`);
    const g = await res.json();
    return { updatedAt: g.updatedAt, user: g.user, commits: g.commits ?? [] };
  } catch {
    if (LOCAL) return fakeGithub();
    return { updatedAt: new Date().toISOString(), user: null, commits: [] };
  }
}

function fakeGithub() {
  const ago = (min) => new Date(Date.now() - min * 60000).toISOString();
  const commits = [
    ["home-server-3d", "Add a robot vacuum that cleans the room", 12],
    ["home-server-3d", "Show recent commits on the desk monitor", 40],
    ["diagram-polish", "Keep label pills off arrowheads", 300],
    ["stable-wallet", "Add the send screen", 1500],
    ["pokepedia", "Cache Pokémon sprites", 2900],
  ].map(([repo, message, min], i) => ({ repo, sha: (0x1a2b3c4 + i * 0x111111).toString(16).slice(0, 7), message, date: ago(min) }));
  return { updatedAt: new Date().toISOString(), user: "example", demo: true, commits };
}

let tick = 0;
function fakeStatus(infra) {
  const names = infra.units.flatMap((u) => (u.containers ?? []).map((c) => c.id));
  const containers = {};
  names.forEach((name, i) => {
    // 대부분 정상, 몇 개는 돌아가며 주의·오류, 하나는 데이터 없음(키 생략).
    const r = (i * 7 + tick * 3) % names.length;
    if (r === 0) return;
    containers[name] = r === 1 ? "error" : r === 2 || r === 5 ? "warn" : "ok";
  });
  tick++;
  const wave = (k) => Math.round((40 + 30 * Math.sin(tick / 3 + k)) * 10) / 10;
  return { updatedAt: new Date().toISOString(), demo: true, containers, host: { cpu: wave(0), mem: wave(2), disk: 23.4 } };
}

export function containerStatus(status, name) {
  return status?.containers?.[name] ?? "unknown";
}

// 유닛 상태 = 컨테이너 중 가장 나쁜 상태. 컨테이너가 없는 유닛은 null.
export function unitStatus(status, unit) {
  const list = (unit.containers ?? []).map((c) => containerStatus(status, c.id));
  if (!list.length) return null;
  if (list.includes("error")) return "error";
  if (list.includes("warn")) return "warn";
  if (list.includes("unknown")) return "unknown";
  return "ok";
}
