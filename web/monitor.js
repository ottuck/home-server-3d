// 벽 모니터(Grafana Cloud 화면)와 책상 모니터(GitHub 최근 커밋)에 그리는 그림, 그리고 눌렀을 때 패널에 띄우는 내용.
// 데이터는 status.js의 fetchHistory()(최근 1시간 호스트 지표)와 fetchGithub()(공개 저장소 최근 커밋)다.

// 칸 순서와 색은 Blender 장식 화면(blender/textures.py dashboard)과 같다: 왼쪽 위부터 초록, 주황, 파랑, 보라.
export const CHARTS = [
  { key: "cpu", label: "CPU", color: "#4cd97a" },
  { key: "mem", label: "메모리", color: "#ff9f33" },
  { key: "net", label: "네트워크", color: "#4d99ff" },
  { key: "disk", label: "디스크", color: "#b373ff" },
];
const FONT = 'system-ui, "Segoe UI", "Malgun Gothic", sans-serif';
const MONO = 'ui-monospace, "Cascadia Code", Consolas, "Malgun Gothic", monospace';

const hasData = (h) => !!h && Object.keys(h.series ?? {}).length > 0;
const last = (list) => list?.findLast((v) => v != null) ?? null;
const lines = (h, c) => (c.key === "net" ? [h.series.netIn, h.series.netOut] : [h.series[c.key]]).filter(Boolean);

export function bytes(v) {
  if (v == null) return "—";
  if (v < 1024) return `${Math.round(v)} B/s`;
  if (v < 1024 ** 2) return `${(v / 1024).toFixed(1)} KB/s`;
  return `${(v / 1024 ** 2).toFixed(1)} MB/s`;
}

function valueText(h, c) {
  if (c.key === "net") {
    const [i, o] = [last(h.series.netIn), last(h.series.netOut)];
    return i == null && o == null ? "—" : `↓${bytes(i)} ↑${bytes(o)}`;
  }
  const v = last(h.series[c.key]);
  return v == null ? "—" : `${v.toFixed(1)}%`;
}

// 세로축 최대값: %는 10 단위로 올리고(10~100), 네트워크는 1·2·5 단위로 올린다.
function scaleMax(ls, c) {
  const m = Math.max(0, ...ls.flat().filter((v) => v != null)) * 1.25;
  if (c.key !== "net") return Math.min(100, Math.max(10, Math.ceil(m / 10) * 10));
  const target = Math.max(m, 1024);
  const p = 10 ** Math.floor(Math.log10(target));
  return [1, 2, 5, 10].map((f) => f * p).find((v) => v >= target);
}
const maxText = (c, max) => (c.key === "net" ? bytes(max) : `${max}%`);

// 빈 칸(null)에서 끊긴 선 조각들. 점은 [x, y](위가 0).
function segments(list, x, y, w, h, max) {
  const out = [];
  let cur = null;
  list.forEach((v, i) => {
    if (v == null) return (cur = null);
    if (!cur) out.push((cur = []));
    cur.push([x + (i / (list.length - 1)) * w, y + h - (Math.min(v, max) / max) * h]);
  });
  return out;
}

// ---------------------------------------------------------------- 벽 모니터(캔버스 텍스처)

export function drawMonitor(canvas, h) {
  const g = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height, bar = 56, pad = 20;
  g.fillStyle = "#090a0d";
  g.fillRect(0, 0, W, H);
  g.fillStyle = "#14171c";
  g.fillRect(0, 0, W, bar);
  g.textBaseline = "middle";
  g.fillStyle = "#e6e6e9";
  g.font = `600 26px ${FONT}`;
  g.fillText("Home Server · 최근 1시간", 24, bar / 2);

  const live = hasData(h);
  const badge = !live ? "데이터 없음" : h.demo ? "예시" : "LIVE";
  g.font = `700 20px ${FONT}`;
  const bw = g.measureText(badge).width + 28;
  g.fillStyle = live ? "#2f9e5a" : "#4a4d52";
  g.beginPath();
  g.roundRect(W - 24 - bw, 14, bw, 28, 14);
  g.fill();
  g.fillStyle = "#ffffff";
  g.fillText(badge, W - 24 - bw + 14, bar / 2 + 1);
  g.fillStyle = "#8b8f98";
  g.font = `500 20px ${FONT}`;
  const time = new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", hour12: false });
  g.fillText(time, W - 24 - bw - 16 - g.measureText(time).width, bar / 2);

  const pw = (W - pad * 3) / 2, ph = (H - bar - pad * 3) / 2;
  CHARTS.forEach((c, k) => {
    const x = pad + (k % 2) * (pw + pad), y = bar + pad + Math.floor(k / 2) * (ph + pad);
    g.fillStyle = "#111318";
    g.beginPath();
    g.roundRect(x, y, pw, ph, 10);
    g.fill();
    g.fillStyle = "#c9c9ce";
    g.font = `600 24px ${FONT}`;
    g.fillText(c.label, x + 18, y + 30);
    if (!live) return;
    g.fillStyle = c.color;
    g.font = `700 26px ${FONT}`;
    const val = valueText(h, c);
    g.fillText(val, x + pw - 18 - g.measureText(val).width, y + 30);

    const cx = x + 18, cy = y + 60, cw = pw - 36, chh = ph - 76;
    g.strokeStyle = "#1e2128";
    g.lineWidth = 2;
    for (let i = 0; i <= 3; i++) {
      g.beginPath();
      g.moveTo(cx, cy + (chh * i) / 3);
      g.lineTo(cx + cw, cy + (chh * i) / 3);
      g.stroke();
    }
    const ls = lines(h, c), max = scaleMax(ls, c);
    ls.forEach((list, i) => {
      for (const seg of segments(list, cx, cy, cw, chh, max)) {
        if (i === 0 && seg.length > 1) {
          g.globalAlpha = 0.18;
          g.fillStyle = c.color;
          g.beginPath();
          g.moveTo(seg[0][0], cy + chh);
          for (const [px, py] of seg) g.lineTo(px, py);
          g.lineTo(seg.at(-1)[0], cy + chh);
          g.fill();
        }
        g.globalAlpha = i === 0 ? 1 : 0.6;
        g.strokeStyle = c.color;
        g.lineWidth = 3;
        g.setLineDash(i === 0 ? [] : [8, 6]);
        g.beginPath();
        seg.forEach(([px, py], j) => (j ? g.lineTo(px, py) : g.moveTo(px, py)));
        g.stroke();
        g.setLineDash([]);
        g.globalAlpha = 1;
      }
    });
    g.fillStyle = "#6c707a";
    g.font = `500 16px ${FONT}`;
    g.fillText(maxText(c, max), cx + 4, cy + 12);
  });
}

// ---------------------------------------------------------------- 패널 차트(SVG)

export function chartsHTML(h) {
  if (!hasData(h)) return `<div class="note">기록을 불러오지 못했습니다.</div>`;
  const W = 300, H = 64;
  return CHARTS.map((c) => {
    const ls = lines(h, c), max = scaleMax(ls, c);
    const pts = (seg) => seg.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join("L");
    const paths = ls.map((list, i) => segments(list, 0, 2, W, H - 2, max).map((seg) =>
      (i === 0 && seg.length > 1 ? `<path d="M${seg[0][0].toFixed(1)},${H}L${pts(seg)}L${seg.at(-1)[0].toFixed(1)},${H}Z" fill="${c.color}" opacity=".16"/>` : "") +
      `<path d="M${pts(seg)}" fill="none" stroke="${c.color}" stroke-width="1.6" vector-effect="non-scaling-stroke"` +
      `${i ? ' stroke-dasharray="4 3" opacity=".75"' : ""}/>`).join("")).join("");
    const grid = [1, 2].map((k) => `<line x1="0" x2="${W}" y1="${(H * k) / 3}" y2="${(H * k) / 3}" class="grid"/>`).join("");
    const note = c.key === "net" ? "실선 받기 · 점선 보내기" : "1시간 전";
    return `<div class="chart"><div class="chart-h"><span>${c.label}</span><b style="color:${c.color}">${valueText(h, c)}</b></div>` +
      `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${grid}${paths}</svg>` +
      `<div class="chart-x"><span>${note}</span><span>최대 ${maxText(c, max)} · 지금</span></div></div>`;
  }).join("");
}

// ---------------------------------------------------------------- 책상 모니터: GitHub 최근 커밋

export function ago(date) {
  const min = Math.max(0, Math.round((Date.now() - new Date(date)) / 60000));
  if (min < 1) return "방금";
  if (min < 60) return `${min}분 전`;
  if (min < 60 * 24) return `${Math.round(min / 60)}시간 전`;
  return `${Math.round(min / 60 / 24)}일 전`;
}

const esc = (t) => String(t).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
const fit = (g, text, w) => {
  if (g.measureText(text).width <= w) return text;
  while (text && g.measureText(text + "…").width > w) text = text.slice(0, -1);
  return text + "…";
};

// 편집기 옆 터미널에서 `git log`를 띄운 모습. 와이드 모니터(21:9) 그림이다.
export function drawCommits(canvas, gh) {
  const g = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height, bar = 64, pad = 40;
  g.fillStyle = "#0d1117";
  g.fillRect(0, 0, W, H);
  g.fillStyle = "#161b22";
  g.fillRect(0, 0, W, bar);
  ["#ff5f57", "#febc2e", "#28c840"].forEach((c, i) => {
    g.fillStyle = c;
    g.beginPath();
    g.arc(36 + i * 34, bar / 2, 10, 0, Math.PI * 2);
    g.fill();
  });
  g.textBaseline = "middle";
  g.fillStyle = "#8b949e";
  g.font = `500 26px ${MONO}`;
  g.fillText(`${gh.user ?? "github"} — git log · 최근 공개 커밋`, 150, bar / 2);

  const line = 58;
  let y = bar + 44;
  g.font = `500 30px ${MONO}`;
  for (const c of gh.commits) {
    if (y > H - 30) break;
    let x = pad;
    g.fillStyle = "#e3b341";
    g.fillText(c.sha, x, y);
    x += g.measureText(c.sha).width + 22;
    g.fillStyle = "#79c0ff";
    g.fillText(c.repo, x, y);
    x += g.measureText(c.repo).width + 22;
    const when = ago(c.date);
    g.fillStyle = "#7d8590";
    const ww = g.measureText(when).width;
    g.fillText(when, W - pad - ww, y);
    g.fillStyle = "#e6edf3";
    g.fillText(fit(g, c.message, W - pad - ww - 30 - x), x, y);
    y += line;
  }
}

export function commitsHTML(gh) {
  if (!gh?.commits?.length) return `<div class="note">커밋을 불러오지 못했습니다.</div>`;
  const base = gh.user && !gh.demo ? `https://github.com/${gh.user}` : null;
  const items = gh.commits.map((c) => {
    const body = `<div class="commit-h"><span>${esc(c.repo)}</span><span>${ago(c.date)}</span></div><div class="commit-m">${esc(c.message)}</div>`;
    return base ? `<li><a href="${base}/${encodeURIComponent(c.repo)}/commit/${esc(c.sha)}" target="_blank" rel="noopener">${body}</a></li>` : `<li>${body}</li>`;
  }).join("");
  const more = base ? `<div class="note"><a href="${base}" target="_blank" rel="noopener">GitHub에서 더 보기 →</a></div>` : "";
  return `<ul class="commits">${items}</ul>${more}`;
}
