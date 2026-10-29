// web/data/ 에 장면 파일을 복사한다. web/ 하나만 배포하면 되도록 하기 위함.
// Cloudflare Pages: 빌드 명령 `node web/sync.mjs`, 출력 디렉터리 `web`.
// 로컬: `node web/sync.mjs` 후 web/ 를 아무 정적 서버로 띄운다.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const web = dirname(fileURLToPath(import.meta.url));
const root = join(web, "..");
const out = join(web, "data");

mkdirSync(out, { recursive: true });
for (const [src, dst] of [
  ["assets/rack.glb", "rack.glb"],
  ["shared/infra.json", "infra.json"],
]) {
  copyFileSync(join(root, src), join(out, dst));
  console.log(`${src} -> web/data/${dst}`);
}
