# Home Server 3D — 설계 결정

실제 홈서버(Lightsail `quant-lab-02`)를 아이소메트릭 미니어처 서버실로 보여 주는 웹 대시보드. 먼저 장면의 완성도를 확보한 뒤 실제 모니터링 데이터를 연결한다.

## 장면 구성

- **랙 1대 = quant-lab-02 인스턴스.** 서비스는 랙에 꽂힌 장비(유닛)이고, 컨테이너 하나가 LED 하나다.
- 장비 목록의 기준은 [`shared/infra.json`](../shared/infra.json)이다. Blender와 웹이 같은 파일을 읽는다. `containers` 값은 cAdvisor `container` 라벨이다(2026-10-29 실측, 13개).
- `decor: true`는 실제 장비가 아닌 장식이다(빈 패널, UPS). UI에서 실제 장비와 구분한다.
- 서버 밖에 있는 서비스(Grafana Cloud, Sentry)는 랙에 넣지 않는다. 방 안의 벽 모니터나 창 너머 요소로 표현한다(전체 방 단계에서 제작).
- UR MCP는 이 서버에 없다. 어디서 돌고 있는지 확인한 뒤 배치한다.

## 3D 제작 (Blender 5.2.3, Python, 헤드리스)

- 실행: `blender -b --factory-startup --python blender/build_rack.py -- --theme day|night --out <png> [--glb assets/rack.glb] [--scale 0.7 --target x y z]`
- Blender는 포터블 판을 `C:\Users\vison\tools\blender-5.2.3-windows-x64`에 둔다. Intel Arc 드라이버가 오래되어 Cycles는 CPU로 그린다(1200px 기준 약 1분).
- 좌표: 정면 -Y, 위 +Z, 미터 단위. 1U = 44.5mm, 전면판 19인치, 랙 외곽 0.66 × 0.66m, 22U.
- GLB 노드 이름 규칙: `unit__<id>`(extras에 `kind`, `decor`), `led__<container>`. 웹은 이 이름으로 LED 색을 바꾼다.
- 낮/밤은 같은 모델을 쓰고 조명과 LED 밝기만 바꾼다. 밤에는 랙 앞 윗프레임 아래의 숨은 조명과 블룸을 켠다.

## 상태 색

정상 녹색, 주의 주황, 오류 빨강, 데이터 없음 회색(`rack.STATUS_COLOR`). 데이터가 없으면 절대 정상으로 칠하지 않는다. 렌더 이미지의 LED는 예시다.

## 데이터 경로 (Phase 4)

Cloudflare Pages(정적 웹)와 Cloudflare Worker를 쓴다. Worker가 읽기 전용 Grafana Cloud 토큰으로 정해진 PromQL만 대신 조회한다. 접근은 Cloudflare Access로 막는다. Lightsail 서버에는 아무것도 추가하지 않는다.

## 남은 일

- 웹 로딩 전에 GLB 최적화: 현재 메시 727개, 2.6MB. 장비별·재질별로 합치고 meshopt로 압축한다.
- 전체 방: 책상, 선반, 식물(CC0 에셋 검토), 창, 벽 모니터. 웹용으로는 조명을 Blender에서 굽는다(bake).
