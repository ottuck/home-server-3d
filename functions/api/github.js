// GET /api/github: 책상 모니터에 띄우는 공개 저장소의 최근 커밋.
// GitHub 커밋 검색 한 번으로 받아 10분 캐시한다. 공개 데이터라 토큰 없이 부르고, GITHUB_TOKEN이 있으면 붙인다.
// 응답: { updatedAt, user, commits: [{ repo, sha, message, date }] }. 실패하면 commits가 빈 배열이다.
import { cachedJson } from "../_lib/cache.js";

const USER = "ottuck";
const TTL = 600;
const FAIL_TTL = 60;
const LIMIT = 10; // 보여 줄 커밋 수
const PER_REPO = 4; // 한 저장소가 목록을 다 차지하지 않게

export const onRequestGet = cachedJson("/api/github", async (env) => {
  const updatedAt = new Date().toISOString();
  try {
    return { data: { updatedAt, user: USER, commits: await recentCommits(env) }, ttl: TTL };
  } catch (e) {
    console.error("github", e);
    return { data: { updatedAt, user: USER, commits: [] }, ttl: FAIL_TTL };
  }
});

async function recentCommits(env) {
  const headers = { accept: "application/vnd.github+json", "user-agent": "home-server-3d", "x-github-api-version": "2022-11-28" };
  if (env.GITHUB_TOKEN) headers.authorization = `Bearer ${env.GITHUB_TOKEN}`;
  const url = `https://api.github.com/search/commits?q=author:${USER}&sort=author-date&order=desc&per_page=100`;
  const res = await fetch(url, { headers, signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error(`github ${res.status}`);
  const { items = [] } = await res.json();
  const perRepo = new Map();
  const out = [];
  for (const it of items) {
    // 자기 공개 저장소의 커밋만 싣는다
    if (it.repository.private || it.repository.owner.login !== USER) continue;
    const repo = it.repository.name;
    if ((perRepo.get(repo) ?? 0) >= PER_REPO) continue;
    perRepo.set(repo, (perRepo.get(repo) ?? 0) + 1);
    out.push({ repo, sha: it.sha.slice(0, 7), message: it.commit.message.split("\n")[0].slice(0, 120), date: it.commit.author.date });
    if (out.length === LIMIT) break;
  }
  return out;
}
