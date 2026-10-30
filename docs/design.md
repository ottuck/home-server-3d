# 설계 결정

Lightsail 서버 한 대를 3D 서버실로 보여 주는 웹 페이지. 장면의 완성도를 먼저 확보하고, 그다음 실제 모니터링 데이터를 연결했다.

## 화면

- **랙 = 서버 한 대, 장비 = 서비스, LED = 컨테이너 하나.**
- 상태 색은 정상 초록, 주의 주황, 오류 빨강, 데이터 없음 회색이다. 데이터가 없으면 절대 정상으로 칠하지 않는다.
- 공개 페이지이므로 실제 호스트 이름과 cAdvisor 컨테이너 이름은 화면과 응답에 싣지 않는다. 호스트는 `AWS Lightsail` / `Home Server · 2 GB`로, 컨테이너는 공개 id로 표시한다.
- 서버 밖에서 도는 서비스는 랙에 넣지 않는다. Grafana Cloud는 뒤 벽 모니터, GitHub는 책상 모니터로 둔다. Sentry 태블릿은 방 분위기에 맞게 인테리어 스피커로 바꿨고, Sentry는 패널의 외부 서비스 목록에만 남긴다.
- 낮/밤은 보는 사람의 현지 시각으로 정한다(06~18시 낮, 1분마다 확인). 버튼을 누르면 자동 전환을 멈춘다.
- 방 배치(3.4 × 2.8m, 벽은 뒤와 왼쪽):

| 위치 | 소품 |
| --- | --- |
| 뒤 벽 | 창(블라인드), 랙, Grafana 모니터, 수납장(탁상등, 스피커, 화분), 로봇 청소기 충전대 |
| 왼쪽 벽 | 책상(와이드 모니터), 의자, 선반, HOME LAB 간판 |
| 앞쪽 | 러그, 안락의자, 협탁 |
| 그 밖 | 화분 4개, 조명 4개(스탠드, 탁상등 2, 벽등), 랙으로 이어지는 천장 케이블 트레이 |

화면 속 그래프·코드와 창밖 풍경은 장식이다(`blender/textures.py`가 numpy로 그린다). 창밖 그림은 창 뒤 평면과 비율(1.5 × 1.6m)을 맞춰 늘어나지 않게 하고, 밤에는 달과 별, 드문드문 켜진 창만 둔다.

## 장비 목록 (`shared/infra.json`)

Blender, 웹, 상태 API가 같은 파일을 읽는다.

| 필드 | 뜻 |
| --- | --- |
| `id` | 컨테이너의 공개 이름. LED 노드 이름과 API 응답 키로 쓴다 |
| `name` | 화면 표시 이름(api, worker 등) |
| `source` | cAdvisor `container` 라벨. 상태 API만 쓴다 |
| `decor` | 실제 장비가 아닌 장식(빈 패널, UPS) |

`web/sync.mjs`가 웹으로 복사할 때 `host.id`와 `source`를 뺀다.

## 3D 제작 (Blender 5.2, 헤드리스)

```
blender -b --factory-startup --python blender/build_room.py -- --theme day|night --out <png> [--glb assets/scene.glb]
blender -b --factory-startup --python blender/build_rack.py -- --theme day|night --out <png> [--glb assets/rack.glb]
```

| 파일 | 역할 |
| --- | --- |
| `lib.py` | 도형, 재질 |
| `rack.py` | 랙 |
| `props.py` | 소품 |
| `room.py` | 벽, 배치, 조명 |
| `stage.py` | 카메라, 렌더 설정 |
| `export.py` | GLB 최적화 |

- 좌표는 정면 -Y, 위 +Z, 미터 단위. 랙은 22U(1U = 44.5mm), 외곽 0.66 × 0.66m.
- GLB는 낮 테마 재질로 내보내고 Draco로 압축한다(`scene.glb` 약 1.5MB). 낮/밤은 같은 모델에서 조명과 발광만 바꾼다.
- 바닥은 이미지 텍스처를 쓴다. 절차 텍스처는 GLB로 나가지 않는다.
- 화분과 컵은 단면을 돌려 만든다(`lib.lathe`). 벽 두께와 테두리, 굽이 보이고, 화분은 네 가지 모양(받침 있는 테라코타, 둥근 도자기, 굽 있는 원통, 곧은 원통)이다.

웹이 찾는 GLB 노드 이름:

| 이름 | 뜻 |
| --- | --- |
| `unit__<id>` | 장비(extras에 `kind`, `decor`). 몸체는 `<id>_body` |
| `led__<컨테이너 id>` | 상태 LED |
| `*_screen` | 화면. 웹이 실시간 그림으로 바꾼다 |
| `skyline` | 창밖 풍경. 밤 그림은 `assets/textures/skyline_night.png` |
| `part__<이름>` | 웹에서 움직이는 부분(청소기, 블라인드 살, 의자 윗부분, 쿠션, 책 덮개). 원점이 회전축이고 회전·크기는 메시에 굳혀 노드는 위치만 갖는다 |
| `prop__<소품>`, `rack_frame`, `room_shell` | 나머지를 합친 메시 |

## 웹 뷰어 (`web/`, three.js, 빌드 없음)

- 카메라는 Blender와 같은 정사영 구도(tilt 58°, yaw 40°)다. 회전은 좌우 ±25°, 상하 -14~+10°, 확대는 0.9~4배로 제한하고, 팬은 방 바닥 안으로 묶는다.
- Blender 조명은 GLB에 들어가지 않아서 뷰어가 같은 자리에 다시 둔다. 밤 분위기의 기준은 Cycles 밤 렌더(`docs/renders/room_night.png`)다.
- glTF로 옮기면 clearcoat가 거울처럼 매끈해져서 거칠기를 올린다(바닥 0.22, 나머지 0.4).
- 벽에 붙이는 소품은 벽면과 같은 평면에 두지 않는다. 웹에서는 벽에 가려진다.
- 링크 미리보기(Open Graph)는 밤 렌더를 1200×630으로 줄인 `web/og.png`를 쓴다(`blender/og_image.py`). 렌더를 다시 만들면 이것도 다시 만든다. 파비콘은 랙 한 대를 그린 `web/favicon.svg`이고, PNG(32px, 180px)는 그 SVG를 resvg로 굽는다.
- 조명 네 개와 간판은 누르면 켜지고 꺼진다. 갓·전구·간판 재질을 조명마다 복제해 따로 칠하고, 고르기 쉽게 투명 상자로 누른 곳을 찾는다. 낮/밤을 바꾸면 그 테마 기본(낮 꺼짐, 밤 켜짐)으로 돌아간다.
- 로봇 청소기는 누르거나 90~150초마다 충전대를 떠나 바닥 세 곳을 돌며 제자리에서 한 바퀴씩 돌고, 충전대 앞에서 돌아서서 후진해 들어간다. 청소 중에 누르면 바로 돌아간다. LED는 청소 중 파랑, 충전 중 초록이다. 자리는 가구 다리를 피해 곧게 오갈 수 있고 기본 구도에서 보이는 곳만 골랐다. (처음엔 고양이였지만 발이 없어 움직임이 청소기 같아서 바꿨다.)
- 블라인드, 의자, 책은 누를 때마다 목표 값이 바뀌고 실제 값이 그쪽으로 빠르게 따라가다 천천히 멈춘다. 안락의자 쿠션은 눌린 뒤 감쇠 진동으로 제 모양을 찾는다. 블라인드를 내리면 창 조명이 75% 줄어든다.
- 소품에는 마우스를 올려도 이름표를 띄우지 않는다. 손가락 커서와 눌렀을 때의 움직임으로 충분하다(랙 장비와 벽 모니터만 이름표를 띄운다).

## 상태 API (`functions/api/status.js`)

Cloudflare Pages 하나로 정적 웹과 `GET /api/status`를 함께 낸다. Lightsail 서버에는 아무것도 추가하지 않는다.

- **조회:** Grafana Cloud Prometheus를 읽기 전용 토큰(scope `metrics:read`)으로 부른다. 신호 전부를 쿼리 하나로 받는다(`label_replace`로 `q` 라벨을 붙여 구분).
- **비밀 값:** `GRAFANA_PROM_URL`, `GRAFANA_PROM_USER`, `GRAFANA_PROM_TOKEN`. 로컬은 `.dev.vars`(커밋 금지), 운영은 Pages Secret.
- **캐시:** 60초(Cache API + isolate 메모리). 실패하면 한 번 더 시도하고, 그래도 실패하면 200으로 빈 상태를 10초만 캐시한다.
- **응답:** `{ updatedAt, containers: { [id]: "ok" | "warn" | "error" }, host: { cpu, mem, disk } }`. 모르는 값은 키를 빼고, 웹은 그 컨테이너를 회색으로 칠한다. 라벨, 호스트 이름, IP, 쿼리는 싣지 않는다.

상태 규칙(지표는 60초마다 들어온다):

| 조건 | 결과 |
| --- | --- |
| 조회 실패, 또는 호스트 지표가 3분 넘게 없음 | 컨테이너 키 전부 생략(회색) |
| 컨테이너 지표가 없거나 3분 넘게 끊김 | error |
| healthcheck가 3분 내내 실패 | error |
| 10분 안에 (재)시작, 또는 메모리 한도의 90% 이상 | warn |
| 그 밖 | ok |

- `container_oom_events_total`은 이 서버에서 믿을 수 없어 쓰지 않는다.
- `quant-lab-demo-seeder`는 일회성이 아니라 계속 떠 있는 컨테이너라서 같은 규칙을 쓴다.
- 호스트 %: CPU는 5분 평균 `1 - idle`, 메모리는 `1 - MemAvailable/MemTotal`, 디스크는 `/` 기준. 소수 1자리.
- 웹(`web/status.js`)은 `?demo=1`이거나 localhost에서 API가 없으면 예시 데이터(`demo: true`)를 쓴다.

### 벽 모니터 (`functions/api/history.js`, `web/monitor.js`)

- `GET /api/history`: 최근 1시간 호스트 지표를 1분 간격 61칸으로 돌려준다(`query_range`, 쿼리 하나). 서버 전체 합계만 싣는다.
  - `cpu`, `mem`, `disk`는 %, `netIn`, `netOut`은 바이트/초(인터페이스는 `lo`, `tailscale*`, `veth*`, `docker*`, `br-*` 제외). 빈 칸은 `null`.
  - 캐시와 실패 처리는 상태 API와 같다(공통 코드 `functions/_lib/prom.js`).
- 웹은 GLB의 `screen_grafana_screen` 그림을 1280×720 캔버스로 바꿔 1분마다 다시 그린다. 칸 순서와 색은 Blender 장식 화면과 같다(CPU 초록, 메모리 주황, 네트워크 파랑, 디스크 보라).
- 모니터나 패널의 "Grafana Cloud" 칩을 누르면 회전 한계 안에서 가장 정면에 가까운 각도로 다가가고, 패널에 큰 차트(SVG)를 연다.
- 세로축은 %면 10 단위(10~100), 네트워크면 1·2·5 단위로 최대값의 1.25배까지 올린다.

### 책상 모니터 (`functions/api/github.js`)

- `GET /api/github`: GitHub 커밋 검색(`author:ottuck`, 최신순) 한 번으로 자기 공개 저장소의 최근 커밋 10개를 돌려준다. 한 저장소는 4개까지만 넣어 여러 프로젝트가 보이게 한다. 이벤트 API는 이제 커밋 메시지를 싣지 않아 쓰지 않는다.
- 공개 데이터라 토큰 없이 부르고 10분 캐시한다(실패하면 1분). 호출 제한에 걸리면 Pages Secret `GITHUB_TOKEN`(권한 없는 읽기 전용 토큰)을 넣으면 된다.
- 웹은 와이드 모니터(21:9)를 1680×720 캔버스로 바꿔 `git log` 터미널처럼 그린다. 커밋을 못 받으면 원래 장식 그림(코드)을 그대로 둔다. 누르면 오른쪽을 보는 각도로 다가가고 패널에 커밋 링크 목록을 연다.
- 공통 캐시 코드는 `functions/_lib/cache.js`로 옮겼다(상태·기록·GitHub API가 함께 쓴다).

## 남은 일

- 웹 조명이 Cycles와 차이가 크면 SSAO나 조명 굽기(낮/밤 두 벌)를 검토한다.
