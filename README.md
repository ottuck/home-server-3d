# Home Server 3D

AWS Lightsail 서버 한 대를 작은 3D 서버실로 꾸민 웹 페이지입니다. 방 안 랙에 꽂힌 장비의 LED가 실제 컨테이너 상태에 따라 켜지기 때문에, 서버가 지금 어떤지 한눈에 볼 수 있습니다.

<p align="center">
  <a href="https://server.portfolio-hub.dev"><img src="https://img.shields.io/badge/%EB%9D%BC%EC%9D%B4%EB%B8%8C_%ED%8E%98%EC%9D%B4%EC%A7%80_%EB%B3%B4%EA%B8%B0-server.portfolio--hub.dev-2f9e6e?style=for-the-badge" alt="라이브 페이지 보기: server.portfolio-hub.dev" height="36"></a>
  <br>
  <sub>실제 서버 상태가 1분 단위로 반영됩니다. 주소 뒤에 <code>?demo=1</code>을 붙이면 예시 데이터로 볼 수 있습니다.</sub>
</p>

| 낮 | 밤 |
| --- | --- |
| ![낮의 방](docs/renders/room_day.png) | ![밤의 방](docs/renders/room_night.png) |
| ![낮의 랙](docs/renders/rack_day.png) | ![밤의 랙](docs/renders/rack_night.png) |

## 무엇을 볼 수 있나요

- **랙 하나가 서버 한 대입니다.** 랙에 꽂힌 장비 하나가 서비스 하나이고, 장비의 LED 하나가 컨테이너 하나입니다.
- **LED 색이 컨테이너 상태입니다.** 정상은 초록, 주의는 주황, 오류는 빨강, 데이터가 없으면 회색으로 켜집니다. 데이터가 없을 때 정상으로 칠하는 일은 없습니다.
- **오른쪽 패널**에서 CPU·메모리·디스크 사용률과 서비스별 상태를 볼 수 있습니다. 서비스를 누르면 카메라가 랙으로 다가갑니다.
- **낮과 밤**은 보는 사람의 시각에 맞춰 바뀝니다(오전 6시~오후 6시는 낮). 화면 오른쪽 위의 해·달 스위치로 직접 바꿀 수도 있습니다.
- **벽 모니터**에는 최근 1시간의 실제 CPU·메모리·네트워크·디스크 그래프가 1분마다 그려집니다. 모니터를 누르면 카메라가 다가가고 패널에 큰 차트가 열립니다.
- **책상 모니터**에는 GitHub 공개 저장소의 최근 커밋이 터미널의 `git log`처럼 떠 있습니다. 누르면 패널에 목록이 열리고, 각 커밋으로 바로 갈 수 있습니다.
- **방 안 물건도 눌러 볼 수 있습니다.** 무엇이 어떻게 움직이는지는 직접 눌러 보세요.
- 서버 밖에서 돌아가는 서비스는 랙에 넣지 않았습니다. Grafana Cloud는 벽 모니터로, GitHub는 책상 모니터로 보여 줍니다.
- **카메라**는 드래그로 돌리고 휠로 확대합니다. 키보드로는 방향키나 WASD로 옮기고, Q/E로 돌리고, +/-로 확대합니다. Space를 누른 채 끌어도 화면이 옮겨집니다.

## 구성

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/architecture-dark.svg">
  <img src="docs/architecture.svg" alt="구성도: 방문자는 Cloudflare Pages의 3D 웹 뷰어를 엽니다. 웹 뷰어가 같은 곳의 상태 API를 부르면, 상태 API가 Grafana Cloud에 PromQL로 Lightsail 서버의 지표를 물어 공개용 상태로 요약해 돌려줍니다. 3D 장면은 개발 PC의 Blender에서 만들어 git push로 배포합니다.">
</picture>

- 3D 장면은 Blender Python 스크립트로 만들어 GLB 파일로 내보내고, 웹에서는 three.js로 띄웁니다.
- 상태 API가 Grafana Cloud에서 서버 지표를 읽어 컨테이너마다 정상·주의·오류만 남겨 돌려줍니다. 조회 토큰과 실제 서버·컨테이너 이름은 브라우저로 나가지 않습니다.
- 조회 결과를 1분 동안 캐시하므로, 방문자가 많아도 Grafana Cloud를 부르는 횟수는 늘지 않습니다.
- 이 프로젝트를 위해 서버에 따로 설치한 것은 없습니다. 원래 쓰던 모니터링(Grafana Alloy)이 보내는 지표를 그대로 읽습니다.

## 기술 스택

| 구분 | 사용 기술 |
| --- | --- |
| 3D 제작 | Blender 5.2 (Python 스크립트로 장면 생성, Cycles 렌더) |
| 3D 파일 | glTF(GLB), Draco 압축 |
| 웹 | three.js 0.170, HTML, CSS, JavaScript (빌드 도구 없이 ES 모듈과 import map) |
| 상태 API | Cloudflare Pages Functions, Cache API, GitHub REST API(커밋 검색) |
| 모니터링 데이터 | Grafana Cloud (Prometheus, PromQL), Grafana Alloy, cAdvisor |
| 배포 | Cloudflare Pages (GitHub에 push하면 자동 배포) |
| 개발 도구 | Node.js, Wrangler, Git / GitHub |

## 폴더 구조

```
blender/     3D 장면을 만드는 Blender Python 스크립트
assets/      내보낸 GLB와 텍스처
web/         웹 뷰어 (three.js, 정적 파일)
functions/   상태 API (Cloudflare Pages Functions)
shared/      장비·컨테이너 목록 (Blender, 웹, 상태 API가 함께 읽음)
docs/        설계 기록, 구성도, 렌더 이미지
```

## 내 서버로 쓰기

이 저장소를 포크해서 내 서버의 서버실로 바꿀 수 있습니다. 비밀 값을 넣기 전에는 예시 데이터로 돌아가므로, 배포부터 해 두고 하나씩 채워도 됩니다.

> **가장 쉬운 방법은 포크한 뒤 AI 코딩 도구(Claude Code 등)에게 맡기는 것입니다.** 아래 단계가 길어 보여도 대부분 설정 파일과 코드를 고치는 일이라 AI가 잘 처리합니다. 3D 장면도 Blender를 직접 만질 필요 없이 Python 스크립트로 만들어지므로, AI가 코드만 고쳐서 장비 구성이나 소품을 바꿀 수 있습니다.
>
> 예) "이 저장소를 내 서버용으로 바꿔 줘. 서버에는 nginx, api, postgres 컨테이너가 있고 Grafana Cloud로 지표를 보내고 있어. README의 '내 서버로 쓰기'를 따라 해 줘."

1. **장비 목록 고치기.** [`shared/infra.json`](shared/infra.json)에 서버 이름(`host`), 랙에 꽂을 장비(`units`), GitHub 아이디(`site.github`)를 적습니다.
   - 장비 하나가 서비스 하나이고, `containers`의 항목 하나가 LED 하나입니다.
   - `kind`는 `server`, `switch`, `patch`, `blank`, `ups` 중 하나입니다. 장비 높이(`u`)의 합은 `host.rackUnits`(기본 22) 이하로 둡니다. 남는 칸은 빈 패널로 채워집니다.
   - 컨테이너 `id`는 화면과 API에 그대로 나오는 공개 이름입니다. 실제 Docker 컨테이너 이름과 같으면 따로 연결할 필요가 없습니다.
   - `site.github`를 비워 두면 책상 모니터에 예시 커밋이 나옵니다.
2. **장비를 바꿨다면 3D 장면 다시 만들기.** 랙은 장비 목록을 읽어 Blender에서 만들어지므로, 장비를 바꾸면 GLB를 다시 내보내야 합니다(아래 "3D 장면 다시 만들기"). 서버 이름이나 GitHub 아이디만 바꿨다면 필요 없습니다.
3. **Cloudflare Pages에 연결하기.** Cloudflare 대시보드에서 포크한 저장소로 Pages 프로젝트를 만들고 아래처럼 설정합니다. 이후로는 push할 때마다 자동으로 배포됩니다.
   - 빌드 명령: `node web/sync.mjs`
   - 빌드 출력 디렉터리: `web`
4. **실제 지표 연결하기(선택).** 서버에서 [Grafana Alloy](https://grafana.com/docs/alloy/)로 node exporter(호스트)와 cAdvisor(컨테이너) 지표를 Grafana Cloud에 보내고 있어야 합니다. Pages 프로젝트의 환경 변수(Secret)에 다음 값을 넣습니다.

   | 이름 | 필수 | 값 |
   | --- | --- | --- |
   | `GRAFANA_PROM_URL` | 예 | Grafana Cloud Prometheus 주소(`https://prometheus-prod-…grafana.net/api/prom`) |
   | `GRAFANA_PROM_USER` | 예 | Prometheus 인스턴스 id(숫자) |
   | `GRAFANA_PROM_TOKEN` | 예 | `metrics:read` 권한만 있는 액세스 정책 토큰 |
   | `CONTAINER_SOURCES` | 아니오 | 공개 id와 실제 컨테이너 이름이 다를 때 연결표. 예: `{"edge-caddy":"caddy"}` |
   | `PROM_CADVISOR_SELECTOR` | 아니오 | 컨테이너 지표를 고르는 라벨. 기본값 `job="integrations/cadvisor"` |
   | `PROM_NODE_SELECTOR` | 아니오 | 호스트 지표를 고르는 라벨. 기본값 `job="integrations/unix"` |
   | `GITHUB_TOKEN` | 아니오 | GitHub API 호출 한도가 부족할 때 |

5. **링크 미리보기 주소 바꾸기.** [`web/index.html`](web/index.html) 위쪽의 `og:url`, `og:image`를 내 도메인으로 바꿉니다.

## 로컬에서 실행하기

먼저 GLB·텍스처와 장비 목록을 `web/data/`로 복사합니다.

```bash
node web/sync.mjs
```

웹 뷰어만 볼 때는 `web/`을 아무 정적 서버로 띄우면 됩니다. 상태 API가 없으면 예시 데이터로 표시됩니다.

```bash
npx serve web
```

상태 API까지 함께 띄우려면 저장소 루트에서 Wrangler를 실행합니다. 실제 값을 받으려면 `.dev.vars.example`을 `.dev.vars`로 복사해 Grafana Cloud 읽기 전용 토큰을 넣어야 합니다. 토큰이 없으면 예시 데이터로 표시됩니다. 어느 경우든 주소에 `?demo=1`을 붙이면 예시 데이터를 볼 수 있습니다.

```bash
npx wrangler pages dev
```

## 3D 장면 다시 만들기

[Blender 5.2](https://www.blender.org/download/)를 화면 없이 실행합니다. 웹에 쓰는 GLB만 만들 때는 렌더 없이 내보내기만 하므로 GPU가 없어도 금방 끝납니다.

```bash
blender -b --factory-startup --python blender/build_room.py -- --glb assets/scene.glb
```

만든 GLB를 웹으로 복사해 확인한 뒤, `assets/scene.glb`를 커밋하고 push합니다.

```bash
node web/sync.mjs
```

README용 그림을 렌더할 때는 `--theme day` 또는 `--theme night`와 `--out renders/room_day.png`를 붙입니다. 랙만 따로 만들 때는 `blender/build_rack.py`를 씁니다.

설계하면서 정한 내용은 [docs/design.md](docs/design.md)에 정리해 두었습니다.

## 라이선스

[MIT](LICENSE). 포크해서 자유롭게 고쳐 쓰셔도 됩니다.
