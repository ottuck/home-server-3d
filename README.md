# Home Server 3D

AWS Lightsail 홈서버 한 대를 아이소메트릭 3D 미니어처 서버실로 보여 주는 웹 대시보드.

| 낮 | 밤 |
| --- | --- |
| ![낮의 방](docs/renders/room_day.png) | ![밤의 방](docs/renders/room_night.png) |
| ![낮의 랙](docs/renders/rack_day.png) | ![밤의 랙](docs/renders/rack_night.png) |

## 무엇을 보여 주나

- **랙 한 대 = 서버 한 대.** 서버에서 돌아가는 서비스가 랙에 꽂힌 장비이고, 컨테이너 하나가 LED 하나다.
- LED 색은 컨테이너 상태다. 정상 녹색, 주의 주황, 오류 빨강, 데이터 없음 회색.
- 서버 밖에 있는 서비스(Grafana Cloud, Sentry)는 랙이 아니라 벽 모니터와 태블릿 화면으로 둔다.
- 낮/밤 테마를 바꿀 수 있고, 처음에는 OS 다크 모드를 따른다.

장비 목록은 [`shared/infra.json`](shared/infra.json) 하나를 Blender·웹·상태 API가 함께 읽는다. 설계 결정은 [`docs/design.md`](docs/design.md)에 있다.

## 기술 구성

- **3D 모델**: Blender Python 스크립트로 방과 랙을 절차적으로 만들고, Draco로 압축한 GLB로 내보낸다.
- **웹**: three.js(빌드 없음, CDN 임포트맵)가 GLB를 띄우고 조명·낮밤·LED를 다룬다.
- **배포**: Cloudflare Pages(GitHub push 시 자동 배포). Pages Functions가 Grafana Cloud 지표를 서버 쪽에서 조회해 공개용 상태로 요약한다. 토큰과 실제 호스트·컨테이너 이름은 브라우저로 나가지 않는다.

## 로컬 실행

```bash
node web/sync.mjs
```

`assets/`의 GLB·텍스처와 `shared/infra.json`을 `web/data/`로 복사한다. 그다음 `web/`을 아무 정적 서버로 띄운다.

```bash
npx serve web
```

상태 API(`functions/`)까지 함께 띄우려면 Wrangler를 쓴다.

```bash
npx wrangler pages dev web
```

## 3D 장면 다시 만들기

Blender 5.2에서 헤드리스로 실행한다.

```bash
blender -b --factory-startup --python blender/build_room.py -- --theme day --out renders/room_day.png --glb assets/scene.glb
```

`--theme night`로 밤 렌더를 만든다. 랙만 만들려면 `blender/build_rack.py`를 쓴다.
