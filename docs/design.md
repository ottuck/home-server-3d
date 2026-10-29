# Home Server 3D — 설계 결정

실제 홈서버(Lightsail `quant-lab-02`)를 아이소메트릭 미니어처 서버실로 보여 주는 웹 대시보드. 먼저 장면의 완성도를 확보한 뒤 실제 모니터링 데이터를 연결한다.

## 장면 구성

- **랙 1대 = quant-lab-02 인스턴스.** 서비스는 랙에 꽂힌 장비(유닛)이고, 컨테이너 하나가 LED 하나다.
- 장비 목록의 기준은 [`shared/infra.json`](../shared/infra.json)이다. Blender와 웹이 같은 파일을 읽는다. `containers` 값은 cAdvisor `container` 라벨이다(2026-10-29 실측, 13개).
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
  - `unit__<id>`: 장비 단위(extras에 `kind`, `decor`). 몸체는 `unit__<id>_body`
  - `led__<container>`: 컨테이너 상태 LED
  - `*_screen`: 화면. 웹이 실시간 그림으로 바꿔 끼운다
  - `skyline`: 창밖 풍경. 밤 그림은 `assets/textures/skyline_night.png`
  - 나머지: `prop__<소품>`, `rack_frame`, `room_shell`로 합쳐 둔다
- GLB는 낮 테마 재질로 내보내고 Draco로 압축한다(`scene.glb` 메시 54개·817KB, `rack.glb` 메시 34개·414KB). 웹에서는 DRACOLoader가 필요하다.
- 낮/밤은 같은 모델을 쓰고 조명과 LED 밝기만 바꾼다. 밤에는 랙 앞 윗프레임 아래의 숨은 조명과 블룸을 켠다.

## 상태 색

정상 녹색, 주의 주황, 오류 빨강, 데이터 없음 회색(`rack.STATUS_COLOR`). 데이터가 없으면 절대 정상으로 칠하지 않는다. 렌더 이미지의 LED는 예시다.

## 데이터 경로 (Phase 4)

Cloudflare Pages(정적 웹)와 Cloudflare Worker를 쓴다. Worker가 읽기 전용 Grafana Cloud 토큰으로 정해진 PromQL만 대신 조회한다. 접근은 Cloudflare Access로 막는다. Lightsail 서버에는 아무것도 추가하지 않는다.

## 남은 일

- 웹 뷰어(React + R3F): `scene.glb`를 불러 고정 아이소메트릭 카메라, 장비 선택, 낮/밤 전환을 만든다.
- 웹에서 Cycles 분위기를 내려면 조명을 Blender에서 굽는다(bake, 낮/밤 두 벌). 먼저 실시간 조명 + 블룸으로 시작하고 차이를 보고 정한다.
