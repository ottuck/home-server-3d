// web/data/ 에 장면 파일을 복사한다. web/ 하나만 배포하면 되도록 하기 위함.
// Cloudflare Pages: 빌드 명령 `node web/sync.mjs`, 출력 디렉터리 `web`.
// 로컬: `node web/sync.mjs` 후 web/ 를 아무 정적 서버로 띄운다.
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const web = dirname(fileURLToPath(import.meta.url));
const root = join(web, "..");
const out = join(web, "data");

mkdirSync(join(out, "textures"), { recursive: true });
for (const [src, dst] of [
  ["assets/scene.glb", "scene.glb"],
  ["assets/textures/skyline_night.png", "textures/skyline_night.png"],
]) {
  copyFileSync(join(root, src), join(out, dst));
  console.log(`${src} -> web/data/${dst}`);
}

// 공개 웹에는 실제 호스트 이름(host.id)과 cAdvisor 라벨(source)을 싣지 않는다. 지금은 infra.json에도 없지만 혹시 몰라 뺀다.
const infra = JSON.parse(readFileSync(join(root, "shared/infra.json"), "utf8"));
delete infra.$comment;
delete infra.host.id;
for (const u of infra.units) for (const c of u.containers ?? []) delete c.source;
writeFileSync(join(out, "infra.json"), JSON.stringify(infra, null, 2));
console.log("shared/infra.json -> web/data/infra.json (host.id·source 제외)");
