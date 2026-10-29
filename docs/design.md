# Home Server 3D — 설계 결정

실제 홈서버(Lightsail `quant-lab-02`)를 아이소메트릭 미니어처 서버실로 보여 주는 웹 대시보드. 먼저 장면의 완성도를 확보한 뒤 실제 모니터링 데이터를 연결한다.

## 장면 구성

- 화면(간판·HUD)에는 실제 호스트 이름을 쓰지 않고 `AWS Lightsail` / `Home Server · 2 GB`로 표시한다. `host.id`는 데이터 연결용으로만 쓴다.
- **랙 1대 = quant-lab-02 인스턴스.** 서비스는 랙에 꽂힌 장비(유닛)이고, 컨테이너 하나가 LED 하나다.
- 장비 목록의 기준은 [`shared/infra.json`](../shared/infra.json)이다. Blender·웹·상태 API가 같은 파일을 읽는다. 컨테이너마다 공개 `id`(LED 이름·API 키), 화면 표시 `name`(api, worker 등), 서버 전용 `source`(cAdvisor `container` 라벨, 2026-10-29 실측 13개)를 둔다. 웹에 복사할 때(`web/sync.mjs`) `host.id`와 `source`는 뺀다.
- `decor: true`는 실제 장비가 아닌 장식이다(빈 패널, UPS). UI에서 실제 장비와 구분한다.
- 서버 밖에 있는 서비스는 랙에 넣지 않는다. Grafana Cloud는 뒤 벽 모니터, Sentry는 수납장 위 태블릿으로 둔다.
- UR MCP는 이 서버에 없다. 어디서 돌고 있는지 확인한 뒤 배치한다.
- 방(3.4 × 2.8m, 벽은 뒤와 왼쪽)의 구성:
  - 뒤 벽: 창, 랙, Grafana 화면, 수납장
  - 왼쪽 벽: 책상(모니터 2대), 의자, 선반, HOME LAB 간판
  - 앞쪽: 러그, 안락의자, 협탁, 고양이
  - 그 밖에 화분 4개, 조명 4개(스탠드, 탁상등 2, 벽등), 랙으로 이어지는 천장 케이블 트레이
- 화면 속 그래프·코드와 창밖 풍경은 장식이다(`blender/textures.py`, numpy로 그린다).

## 3D 제작 (Blender 5.2.3, Python, 헤드리스)

- 방 전체: `blender -b --factory-startup --python blender/build_room.py -- --theme day|night --out <png> [--glb assets/scene.glb]`
- 랙만: `blender -b --factory-startup --python blender/build_rack.py -- --theme day|night --out <png> [--glb assets/rack.glb] [--scale 0.7 --target x y z]`
- Blender는 포터블 판을 `C:\Users\vison\tools\blender-5.2.3-windows-x64`에 둔다. Cycles는 Arc 130V GPU(oneAPI, 드라이버 32.0.101.9150)로 그린다. 방 1600×1000·128샘플이 약 1분이다.
- 파일 구성:
  - `lib.py`: 도형·재질
  - `rack.py`: 랙
  - `props.py`: 소품
  - `room.py`: 벽·배치·조명
  - `stage.py`: 카메라·렌더 설정
  - `export.py`: GLB 최적화
- 좌표: 정면 -Y, 위 +Z, 미터 단위. 1U = 44.5mm, 전면판 19인치, 랙 외곽 0.66 × 0.66m, 22U.
- GLB 노드 이름 규칙(웹이 이 이름으로 찾는다):
  - `unit__<id>`: 장비 단위(extras에 `kind`, `decor`). 몸체는 `<id>_body`(접두사 없음)
  - `led__<컨테이너 공개 id>`: 컨테이너 상태 LED(예: `led__quant-lab-api`)
  - `*_screen`: 화면. 웹이 실시간 그림으로 바꿔 끼운다
  - `skyline`: 창밖 풍경. 밤 그림은 `assets/textures/skyline_night.png`
  - 나머지: `prop__<소품>`, `rack_frame`, `room_shell`로 합쳐 둔다
- GLB는 낮 테마 재질로 내보내고 Draco로 압축한다(`scene.glb` 메시 54개·1.45MB, 그중 바닥 그림이 약 0.6MB; `rack.glb` 메시 34개·414KB). 웹에서는 DRACOLoader가 필요하다.
- 낮/밤은 같은 모델을 쓰고 조명과 LED 밝기만 바꾼다. 밤에는 랙 앞 윗프레임 아래의 숨은 조명과 블룸을 켠다.

## 웹 뷰어 (`web/`, three.js, 빌드 없음)

- 실행: `node web/sync.mjs`로 `scene.glb`·밤 창밖 그림·`infra.json`을 `web/data/`에 복사한 뒤, `web/`을 정적 서버로 띄운다.
- 카메라: Blender 방 카메라와 같은 정사영 구도(tilt 58°, yaw 40°)다. 회전은 좌우 ±25°, 상하 -14~+10°로 제한하고, 확대는 0.9~4배다. 팬은 방 바닥 안으로 묶는다.
- 조명: Blender 조명은 GLB에 들어가지 않으므로 뷰어가 같은 위치에 다시 둔다(해, 창, 스탠드·책상등·탁상등·벽등, 랙 앞 빛).
- 낮/밤: 조명 세기, 창밖 그림, 전등갓·전구·간판 발광, 화면 밝기, 블룸을 바꾼다. 처음에는 OS 다크 모드를 따른다.
- 바닥은 Blender에서도 이미지 텍스처(`textures.wood_planks`)를 쓴다. 절차 텍스처는 GLB로 나가지 않기 때문이다.
- 밤 분위기의 기준은 Cycles 밤 렌더(`docs/renders/room_night.png`)다. 스탠드는 위아래가 뚫린 전등갓의 주 조명이고, 조명 기구는 그림자를 만들지 않는다.
- Blender 코트(clearcoat)는 glTF에서 거울처럼 매끈해진다. 그래서 뷰어에서 거칠기를 올린다(바닥 0.22, 나머지 0.4). 바닥 코팅은 광택이 예뻐서 유지한다.
- 벽에 붙이는 소품은 벽면과 같은 평면에 두지 않는다. Cycles에서는 보여도 웹에서는 벽에 가려진다.

## 상태 색

정상 녹색, 주의 주황, 오류 빨강, 데이터 없음 회색(`rack.STATUS_COLOR`). 데이터가 없으면 절대 정상으로 칠하지 않는다. 렌더 이미지의 LED는 예시다.

## 데이터 경로 (Phase 4)

Cloudflare Pages 하나로 정적 웹과 상태 API(Pages Functions `functions/api/status.js`, `GET /api/status`)를 함께 낸다. 공개 페이지다. Lightsail 서버에는 아무것도 추가하지 않는다.

- 함수가 Grafana Cloud Prometheus(`/api/prom/api/v1/query`)를 읽기 전용 토큰(access policy `home-server-3d-status-read`, scope `metrics:read`)으로 조회한다. 비밀 값은 `GRAFANA_PROM_URL`·`GRAFANA_PROM_USER`(인스턴스 id)·`GRAFANA_PROM_TOKEN`, 로컬은 `.dev.vars`(커밋 금지, 예시는 `.dev.vars.example`), 운영은 Pages Secret.
- 신호 전부를 쿼리 하나(`label_replace`로 `q` 라벨 구분)로 받고, 결과를 60초 캐시(Cache API + isolate 메모리)한다. 실패하면 한 번 더 시도하고, 그래도 실패하면 200으로 `containers: {}`, `host: {}`를 10초만 캐시한다.
- 응답: `{ updatedAt, containers: { [공개 id]: "ok"|"warn"|"error" }, host: { cpu, mem, disk } }`. `infra.json`의 `source`(cAdvisor 라벨)를 공개 id로 바꾸고, 라벨·호스트 이름·IP·쿼리는 싣지 않는다. 모르는 값은 키를 뺀다(웹은 회색).
- 상태 규칙(스크레이프 60초 기준):
  - 호스트 지표(`node_memory_MemTotal_bytes`)가 3분 넘게 없거나 조회 실패 → 컨테이너 키 전부 생략.
  - 컨테이너 지표(`container_last_seen`)가 없거나 3분 넘게 끊김 → error. healthcheck가 3분 내내 실패(`container_health_state` 0) → error.
  - 10분 안에 (재)시작(`container_start_time_seconds`) 또는 메모리 한도 90% 이상(한도가 있는 컨테이너만) → warn. 그 밖은 ok.
  - `container_oom_events_total`은 이 서버에서 믿을 수 없어 쓰지 않는다.
  - seeder(`quant-lab-demo-seeder`)는 일회성이 아니라 demo-api와 함께 계속 떠 있는 컨테이너(실측)라 같은 규칙을 쓴다.
- 호스트 %: CPU `1 - avg(rate(idle[5m]))`, 메모리 `1 - MemAvailable/MemTotal`, 디스크 `/`의 `1 - avail/size`. 소수 1자리.
- 웹(`web/status.js`)은 `/api/status`를 쓴다. `?demo=1`이거나 localhost에서 API가 없으면 가짜 상태(`demo: true`)를 쓴다. 실제 응답에는 `demo`가 없다.
- 로컬 확인: 저장소 루트에서 `node web/sync.mjs` 후 `npx wrangler pages dev`.

## 남은 일

- 웹에서 더 Cycles 같은 그림자·간접광이 필요하면 SSAO(화면 공간 주변광 가림)나 조명 굽기를 검토한다.
- 웹에서 Cycles 분위기를 내려면 조명을 Blender에서 굽는다(bake, 낮/밤 두 벌). 먼저 실시간 조명 + 블룸으로 시작하고 차이를 보고 정한다.
