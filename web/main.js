import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { GTAOPass } from "three/addons/postprocessing/GTAOPass.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { STATUS_COLOR, fetchStatus, fetchHistory, fetchGithub, containerStatus, unitStatus } from "./status.js";
import { drawMonitor, chartsHTML, drawCommits, commitsHTML } from "./monitor.js";

const REFRESH_MS = 5000;
const HISTORY_MS = 60_000; // 벽 모니터 기록(API가 1분 캐시)
const GITHUB_MS = 600_000; // 책상 모니터 커밋(API가 10분 캐시)
const STATUS_LABEL = { ok: "정상", warn: "주의", error: "오류", unknown: "데이터 없음" };
const RANK = { ok: 0, unknown: 1, warn: 2, error: 3 };

// Blender 좌표 (x, y, z) -> glTF/three 좌표 (x, z, -y)
const B = (x, y, z) => new THREE.Vector3(x, z, -y);

// Blender 방 카메라(build_room.py)와 같은 구도: tilt 58°, yaw 40°, 목표점 (0, 0.1, 1.08), 화면 6.5 × 4.06m.
const TARGET = B(0, 0.1, 1.08);
const TILT = THREE.MathUtils.degToRad(58);
const YAW = THREE.MathUtils.degToRad(40);
const VIEW_DIR = new THREE.Vector3(Math.sin(TILT) * Math.sin(YAW), Math.cos(TILT), Math.sin(TILT) * Math.cos(YAW));
// 모니터를 볼 때는 회전 한계 안에서 화면을 가장 정면에 가깝게 본다(벽 모니터는 앞, 책상 모니터는 오른쪽을 본다)
const MONITOR_DIR = new THREE.Vector3().setFromSphericalCoords(1, TILT - THREE.MathUtils.degToRad(13), YAW - THREE.MathUtils.degToRad(24));
const DESK_DIR = new THREE.Vector3().setFromSphericalCoords(1, TILT - THREE.MathUtils.degToRad(13), YAW + THREE.MathUtils.degToRad(24));
const VIEW_HALF_W = 6.5 / 2;
const VIEW_HALF_H = 4.06 / 2;
// 방 바닥 범위(팬 제한): Blender x[-1.7,1.7], y[-1.4,1.4]
const PAN_MIN = B(-1.7, 1.4, 0.3), PAN_MAX = B(1.7, -1.4, 1.8);

// blender/room.py THEMES의 조명을 three.js 조명으로 옮긴 값. 강도는 눈으로 맞췄다.
const THEMES = {
  day: {
    bg: 0xeee8df, hemi: 1.5, sun: 3.0, env: 0.6, window: 1.2, lamps: true, rack: 0, // 처음 보는 사람에게도 아늑하게 낮에도 조명을 켜 둔다
    screen: 0.7, led: 7, bloom: [0.25, 0.3, 2.2], glow: 1.8, // 햇빛에 묻히지 않게 켠 갓·전구를 더 밝게
  },
  night: {
    bg: 0x1a2340, hemi: 0.07, sun: 0, env: 0.04, window: 0.6, lamps: true, rack: 1.2,
    screen: 1.0, led: 14, bloom: [0.22, 0.3, 1.6], glow: 1, // 밤 블룸은 빛나는 것만 살짝 번지게(벽이 뿌옇게 번지지 않게)
  },
};

const stage = document.getElementById("stage");
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.AgXToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
stage.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;

const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 40);
camera.position.copy(TARGET).addScaledVector(VIEW_DIR, 12);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.copy(TARGET);
controls.enableDamping = true;
controls.screenSpacePanning = true;
controls.minAzimuthAngle = YAW - THREE.MathUtils.degToRad(25);
controls.maxAzimuthAngle = YAW + THREE.MathUtils.degToRad(25);
controls.minPolarAngle = TILT - THREE.MathUtils.degToRad(14);
controls.maxPolarAngle = TILT + THREE.MathUtils.degToRad(10);
controls.minZoom = 0.9;
controls.maxZoom = 5;
controls.addEventListener("change", () => {
  // 방 밖으로 끌려 나가지 않게 목표점을 묶는다
  const t = controls.target;
  const clamped = t.clone().clamp(PAN_MIN.clone().min(PAN_MAX), PAN_MAX.clone().max(PAN_MIN));
  if (!clamped.equals(t)) {
    camera.position.add(clamped.clone().sub(t));
    t.copy(clamped);
  }
});
controls.update();

// ---------------------------------------------------------------- 조명

const hemi = new THREE.HemisphereLight(0xfff6ea, 0xc9a07a, 1);
const sun = new THREE.DirectionalLight(0xfff0dc, 1);
sun.position.copy(TARGET).add(new THREE.Vector3(-0.49, 0.64, 0.59).normalize().multiplyScalar(7));
sun.target.position.copy(TARGET);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -3.5, right: 3.5, top: 3.5, bottom: -3.5, near: 0.5, far: 16 });
sun.shadow.radius = 5;
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.01;
// 창으로 들어오는 빛(방 안쪽, +Z 방향)
const windowLight = new THREE.SpotLight(0xfff0d8, 1, 6, THREE.MathUtils.degToRad(60), 0.9, 1.2);
windowLight.position.copy(B(-0.85, 1.55, 1.45));
windowLight.target.position.copy(B(-0.4, -0.3, 0.2));
// 밤 조명: 스탠드, 책상 등, 탁상등, 벽등(room.py 위치와 같다)
const warm = 0xffa45a; // 2700K 전구색
const lamps = [
  [B(-1.36, -1.08, 1.42), 2.6, 7.5, true], // 스탠드: 방 전체를 밝히는 주 조명(옆 벽이 하얗게 뜨지 않게 세기는 낮추고 넓게)
  [B(-1.43, 0.58, 1.10), 0.7, 2.5, false],
  [B(0.93, 1.20, 0.70), 0.9, 3.0, false],
  [B(-0.13, 1.31, 1.74), 0.9, 3.0, false],
  [B(1.25, -0.68, 1.27), 1.1, 3.0, false], // 안락의자 위 아크 스탠드(갓 안, 전구 아래)
].map(([pos, power, dist, shadow]) => {
  const l = new THREE.PointLight(warm, 0, dist, 1.9); // Cycles처럼 멀어질수록 빨리 어두워지게
  l.position.copy(pos);
  l.userData.power = power;
  if (shadow) {
    l.castShadow = true;
    l.shadow.mapSize.set(1024, 1024);
    l.shadow.radius = 4;
    l.shadow.bias = -0.002;
  }
  return l;
});
// 밤: 랙 앞을 은은하게 비추는 빛(랙 윗프레임 아래 숨은 조명 대신)
const rackLight = new THREE.SpotLight(0xffe2c0, 0, 2.5, THREE.MathUtils.degToRad(45), 0.8, 1.5);
rackLight.position.copy(B(0.35, 0.35, 1.55));
rackLight.target.position.copy(B(0.35, 0.67, 0.55));
scene.add(hemi, sun, sun.target, windowLight, windowLight.target, rackLight, rackLight.target, ...lamps);

// ---------------------------------------------------------------- 렌더 파이프라인

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
// 앰비언트 오클루전: 실시간 렌더는 벽·바닥에서 튕긴 빛(간접광)을 계산하지 않아 구석이 밝게 뜬다.
// 가구가 맞닿은 구석과 밑을 어둡게 해 Cycles 렌더의 깊이감을 흉내 낸다(반경은 미터 단위).
const ao = new GTAOPass(scene, camera, 1, 1);
const aoSamples = matchMedia("(pointer: coarse)").matches ? 8 : 16; // 휴대폰에서는 표본을 줄여 부드럽게
ao.updateGtaoMaterial({ radius: 0.5, distanceExponent: 1.5, thickness: 1, scale: 1.3, samples: aoSamples });
ao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 8, rings: 2, samples: aoSamples });
composer.addPass(ao);
const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), 0.4, 0.4, 0.9);
composer.addPass(bloom);
composer.addPass(new OutputPass());

let halfH = VIEW_HALF_H; // 확대 배율 계산용(zoom 1에서 보이는 높이의 절반)
function resize() {
  // 방 전체(6.5 × 4.06m)가 화면 영역에 들어오게 맞춘다. 세로 화면은 좌우 여백을 줄인다.
  const w = stage.clientWidth, h = stage.clientHeight;
  const a = w / h;
  const fitW = a < VIEW_HALF_W / VIEW_HALF_H;
  const tight = VIEW_HALF_W * 0.84;
  const hw = fitW ? tight : VIEW_HALF_H * a;
  halfH = fitW ? tight / a : VIEW_HALF_H;
  Object.assign(camera, { left: -hw, right: hw, top: halfH, bottom: -halfH });
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  composer.setSize(w, h);
}
new ResizeObserver(resize).observe(stage);
resize();

// ---------------------------------------------------------------- 장면

const leds = new Map(); // 컨테이너 공개 id -> { mesh, status }
const units = new Map(); // unit id -> { object, info, tag }
const mats = new Map(); // 재질 이름 -> 재질(GLB 안에서 공유)
const screens = []; // 화면 재질(*_screen)
let skyline = null; // { material, day, night }
let monitor = null; // 벽 모니터 { screen, parts, canvas, texture }
let history = null;
let desk = null; // 책상 모니터 { screen, parts, canvas, texture, code: 원래 그림 }
let github = null;
let rack = null;
let infra = null;
let status = null;
globalThis.viewer = { leds, units, mats, scene, camera, renderer, controls, get status() { return status; }, get vacuum() { return vacuum; }, get switches() { return switches; }, get toys() { return toys; } }; // 콘솔 디버깅용

function setupScene(gltf, nightSky) {
  const root = gltf.scene;
  root.traverse((o) => {
    if (o.isMesh) {
      const glow = o.name.endsWith("_screen") || o.name === "skyline";
      // 조명 기구는 자기 빛을 가리지 않도록 그림자를 만들지 않는다
      const fixture = ["prop__floor_lamp", "prop__table_lamp", "prop__sconce", "prop__arc_lamp"].includes(o.name);
      o.castShadow = !glow && !fixture;
      o.receiveShadow = !glow;
      for (const m of [o.material].flat()) {
        mats.set(m.name, m);
        // Blender 코트는 glTF에서 거울처럼 매끈해져 점 조명이 바닥에 점으로 맺힌다.
        // 바닥은 은은한 광택을 남기고(Cycles 렌더의 느낌), 나머지는 더 거칠게 한다.
        if (m.clearcoat) m.clearcoatRoughness = Math.max(m.clearcoatRoughness, m.name === "floor_wood" ? 0.22 : 0.4);
      }
      if (o.name.endsWith("_screen")) screens.push(o.material);
      if (o.name === "screen_grafana_screen") setupMonitor(o);
      if (o.name === "desk_mon_screen") setupDesk(o);
      if (o.name === "skyline") {
        nightSky.flipY = false;
        nightSky.colorSpace = THREE.SRGBColorSpace;
        skyline = { material: o.material, day: o.material.map, night: nightSky };
      }
    }
    if (o.name === "rack") rack = o;
    const [kind, id] = o.name.split("__");
    if (kind === "led" && id) {
      // LED 재질은 상태별로 공유되어 있으므로 하나씩 복제해 따로 칠한다.
      o.traverse((m) => {
        if (m.isMesh) {
          m.material = m.material.clone();
          m.castShadow = false;
          leds.set(id, { mesh: m, status: "unknown" });
        }
      });
    } else if (kind === "unit" && id) {
      units.set(id, { object: o, info: infra.units.find((u) => u.id === id) ?? { id, ...o.userData } });
    }
  });
  if (monitor) monitor.parts.push(root.getObjectByName("prop__screen_grafana") ?? monitor.screen);
  scene.add(root);
  root.updateMatrixWorld(true); // 첫 렌더 전에 장비 위치(이름표 기준점)를 계산하려면 필요하다
  makeTags();
  if (desk) {
    // 화면이 작아 누르기 쉽게 테두리까지 덮는 투명 상자를 함께 고른다(위치 계산이 끝난 뒤에 잰다)
    const hit = hitBox(new THREE.Box3().setFromObject(desk.screen), 0.05);
    scene.add(hit);
    desk.parts.push(hit);
  }
  findOccluders(root); // 조명 스위치가 재질을 복제하기 전에(가림 소품의 재질을 먼저 따로 떼어 둔다)
  setupSwitches(root);
  setupRattanLight(root.getObjectByName("prop__table_lamp"));
  setupVacuum(root.getObjectByName("part__vacuum"));
  setupToys(root);
}

// 벽 모니터의 장식 그림을 실제 그래프 캔버스로 바꾼다(glTF UV에 맞춰 flipY 끔).
function setupMonitor(screen) {
  const { canvas, texture } = screenTexture(1280, 720);
  screen.material.map = screen.material.emissiveMap = texture;
  screen.material.needsUpdate = true;
  monitor = { screen, parts: [screen], canvas, texture };
  paintMonitor();
}

function paintMonitor() {
  if (!monitor) return;
  drawMonitor(monitor.canvas, history);
  monitor.texture.needsUpdate = true;
}

function screenTexture(w, h) {
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const texture = new THREE.CanvasTexture(canvas);
  texture.flipY = false;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return { canvas, texture };
}

// 책상 와이드 모니터(21:9)에 GitHub 최근 커밋을 띄운다. 커밋을 못 받으면 원래 장식 그림(코드)을 둔다.
function setupDesk(screen) {
  desk = { screen, parts: [screen], code: screen.material.map, ...screenTexture(1680, 720) };
}

function paintDesk() {
  if (!desk) return;
  const live = github?.commits?.length > 0;
  if (live) {
    drawCommits(desk.canvas, github);
    desk.texture.needsUpdate = true;
  }
  const map = live ? desk.texture : desk.code;
  if (desk.screen.material.map !== map) {
    desk.screen.material.map = desk.screen.material.emissiveMap = map;
    desk.screen.material.needsUpdate = true;
  }
}

// ---------------------------------------------------------------- 테마

let theme = "day";
function applyTheme(name) {
  theme = name;
  const t = THEMES[name];
  document.body.classList.toggle("night", name === "night");
  for (const b of document.querySelectorAll("#theme button")) b.setAttribute("aria-pressed", b.dataset.theme === name);
  scene.background = new THREE.Color(t.bg);
  hemi.intensity = t.hemi;
  sun.intensity = t.sun;
  sun.castShadow = t.sun > 0;
  scene.environmentIntensity = t.env;
  windowLight.color.set(name === "day" ? 0xfff0d8 : 0x8ea4ff);
  for (const s of switches) s.on = t.lamps; // 테마를 바꾸면 눌러서 바꾼 조명도 그 테마 기본으로 돌아간다
  rackLight.intensity = t.rack;
  for (const m of screens) m.emissiveIntensity = t.screen;
  if (skyline) {
    const tex = name === "day" ? skyline.day : skyline.night;
    skyline.material.map = skyline.material.emissiveMap = tex;
    skyline.material.needsUpdate = true;
  }
  [bloom.strength, bloom.radius, bloom.threshold] = t.bloom;
  warmShaders();
}

// 셰이더는 처음 그릴 때 만들어지는데, 그동안 화면이 멈춘다(랙을 처음 확대할 때 1초 넘게 멈췄다).
// 장면 전체와, 랙을 확대하면 반투명해지는 소품의 셰이더를 백그라운드에서 미리 만들어 둔다.
// 조명 구성(테마)이 바뀌면 셰이더도 달라지므로 테마를 정할 때마다 한다.
function warmShaders() {
  if (fade > 0) return; // 소품이 이미 반투명한 중이면 건드리지 않는다
  const faded = [];
  for (const o of occluders) o.traverse((m) => m.isMesh && faded.push([m.material, m.material.transparent]));
  for (const [m] of faded) m.transparent = true;
  // RenderPass는 화면이 아니라 composer 버퍼에 그린다. 톤 매핑·색 공간이 셰이더에 들어가므로 같은 대상으로 만든다.
  const target = renderer.getRenderTarget();
  renderer.setRenderTarget(composer.readBuffer);
  renderer.compileAsync(scene, camera).catch(() => {});
  renderer.setRenderTarget(target);
  // compile은 지금 바로 셰이더를 고르므로 곧장 되돌려도 된다. 되돌린 뒤에는 원래 셰이더를 다시 고르게 한다.
  for (const [m, was] of faded) {
    m.transparent = was;
    m.needsUpdate = true;
  }
}
// 방문자 현지 시각으로 낮(06~18시)·밤을 고르고 1분마다 다시 본다. 버튼을 누르면 그 뒤로는 자동 전환을 멈춘다.
let autoTheme = true;
const clockTheme = () => {
  const h = new Date().getHours();
  return h >= 6 && h < 18 ? "day" : "night";
};
for (const b of document.querySelectorAll("#theme button")) {
  b.onclick = () => {
    autoTheme = false;
    applyTheme(b.dataset.theme);
  };
}

// ---------------------------------------------------------------- 오른쪽 패널

const $ = (id) => document.getElementById(id);
const liveUnits = () => infra.units.filter((u) => !u.decor && u.containers?.length);
const worst = (list) => list.reduce((a, b) => (RANK[b] > RANK[a] ? b : a), "ok");

function renderPanel() {
  const states = liveUnits().map((u) => unitStatus(status, u));
  const overall = status ? worst(states) : "unknown";
  const when = status?.updatedAt ? new Date(status.updatedAt).toLocaleTimeString("ko-KR") : "-";
  const source = !status ? "연결 실패" : status.demo ? "예시 데이터" : "실시간";
  $("overall").innerHTML = `<i class="dot ${overall}"></i><b>${STATUS_LABEL[overall]}</b> · ${source} · ${when}`;

  const host = status?.host ?? {};
  // 차트·커밋 목록은 데이터가 올 때 미리 그려 두고, 화면을 누르면 보이기만 한다(카메라가 움직이는 첫 프레임을 가볍게).
  $("charts").hidden = screenFocus !== "grafana";
  $("commits").hidden = screenFocus !== "desk";

  $("metrics").innerHTML = [["CPU", host.cpu], ["메모리", host.mem], ["디스크", host.disk]].map(([k, v]) => {
    const ok = Number.isFinite(v);
    return `<div class="metric"><div class="k">${k}</div><div class="v">${ok ? Math.round(v) + "%" : "—"}</div>` +
      `<div class="bar"><i style="width:${ok ? Math.min(v, 100) : 0}%"></i></div></div>`;
  }).join("");

  const okCount = states.filter((s) => s === "ok").length;
  $("svc-count").textContent = `${okCount} / ${states.length} 정상`;
  $("services").innerHTML = liveUnits().map((u) => {
    const s = unitStatus(status, u);
    const cs = u.containers.map((c) => [c, containerStatus(status, c.id)]);
    const up = cs.filter(([, st]) => st === "ok").length;
    const kids = u.id === selected
      ? `<div class="kids">${cs.map(([c, st]) => `<div><i class="dot ${st}"></i>${c.name}<span>${STATUS_LABEL[st]}</span></div>`).join("")}</div>`
      : "";
    return `<li class="svc${u.id === selected ? " sel" : ""}" data-id="${u.id}"><div class="row1"><i class="dot ${s}"></i>` +
      `<span class="name">${u.label}</span><span class="count">${up}/${cs.length}</span></div>${kids}</li>`;
  }).join("");

  for (const [id, u] of units) {
    if (!u.tag) continue;
    u.tag.querySelector(".dot").className = `dot ${unitStatus(status, u.info) ?? "unknown"}`;
    u.tag.classList.toggle("sel", id === selected);
  }
}
$("ext-grafana").onclick = () => focusScreen("grafana");
$("ext-github").onclick = () => focusScreen("desk");
$("services").addEventListener("click", (e) => {
  const li = e.target.closest(".svc");
  if (li) select(li.dataset.id === selected ? null : li.dataset.id, true);
});

// ---------------------------------------------------------------- 랙 확대·선택

let focused = false; // 랙 확대
let screenFocus = null; // 확대해 보는 화면: "grafana"(벽 모니터) | "desk"(책상 모니터)
let selected = null;
let anim = null;
const clock = new THREE.Clock();

function flyTo(target, zoom, dir = VIEW_DIR) {
  anim = {
    t0: clock.getElapsedTime(),
    from: { target: controls.target.clone(), position: camera.position.clone(), zoom: camera.zoom },
    to: { target, position: target.clone().addScaledVector(dir, 12), zoom },
  };
}

function stepAnim(t) {
  if (!anim) return;
  const k = Math.min((t - anim.t0) / 0.7, 1);
  const e = k < 0.5 ? 4 * k ** 3 : 1 - (-2 * k + 2) ** 3 / 2;
  controls.target.lerpVectors(anim.from.target, anim.to.target, e);
  camera.position.lerpVectors(anim.from.position, anim.to.position, e);
  camera.zoom = anim.from.zoom + (anim.to.zoom - anim.from.zoom) * e;
  camera.updateProjectionMatrix();
  if (k === 1) anim = null;
}

function focusRack() {
  if (!rack) return;
  const box = new THREE.Box3().setFromObject(rack);
  const c = box.getCenter(new THREE.Vector3());
  const h = box.max.y - box.min.y;
  // 랙과 오른쪽 이름표가 함께 보이도록 목표점을 랙 오른쪽으로 조금 옮긴다
  flyTo(c.add(new THREE.Vector3(0.18, -0.02, 0.1)), THREE.MathUtils.clamp((2 * halfH) / (h * 1.25), 1, 5));
  focused = true;
  screenFocus = null;
  $("back").classList.add("show");
}

function focusScreen(which) {
  const s = which === "desk" ? desk : monitor;
  if (!s) return;
  const box = new THREE.Box3().setFromObject(s.screen);
  const w = Math.hypot(box.max.x - box.min.x, box.max.z - box.min.z);
  // 화면 폭이 보이는 폭의 약 80%가 되게 맞춘다
  flyTo(box.getCenter(new THREE.Vector3()), THREE.MathUtils.clamp((2 * camera.right) / (w * 1.25), 1, 5), which === "desk" ? DESK_DIR : MONITOR_DIR);
  focused = false;
  screenFocus = which;
  select(null);
  $("back").classList.add("show");
  $("panel").scrollTop = 0;
}

// 랙을 확대하면 카메라와 랙 사이에 선 소품(아크 스탠드 등)을 반투명하게 비켜 준다.
// 랙 앞면 여러 점에서 카메라 쪽으로 광선을 쏴 걸리는 소품을 한 번 찾아 둔다.
const occluders = [];
let fade = 0;
function findOccluders(root) {
  const cands = root.children.filter((o) => /^(prop|part)__/.test(o.name) && o.name !== "prop__rug");
  const box = new THREE.Box3().setFromObject(rack);
  const r = new THREE.Raycaster();
  const found = new Set();
  for (let i = 0; i <= 6; i++) {
    for (let j = 0; j <= 8; j++) {
      const p = new THREE.Vector3(
        THREE.MathUtils.lerp(box.min.x, box.max.x, i / 6),
        THREE.MathUtils.lerp(box.min.y, box.max.y, j / 8),
        box.max.z,
      );
      r.set(p, VIEW_DIR);
      for (const h of r.intersectObjects(cands, true)) {
        let o = h.object;
        while (o.parent !== root) o = o.parent;
        found.add(o);
      }
    }
  }
  for (const o of found) {
    o.traverse((m) => {
      if (!m.isMesh) return;
      m.material = m.material.clone(); // 같은 재질을 쓰는 다른 소품까지 투명해지지 않게
      // 투명한 양면 재질을 뒷면·앞면 두 번에 나눠 그리면 three.js가 한쪽 면 셰이더를 남겨 둔다. 한 번에 그리게 한다.
      m.material.forceSinglePass = true;
      m.userData.opacity = m.material.opacity;
      m.userData.shadow = m.castShadow;
    });
    occluders.push(o);
  }
}
const inOccluder = (obj) => { for (let o = obj; o; o = o.parent) if (occluders.includes(o)) return true; return false; };

function stepFade(dt) {
  const goal = focused ? 1 : 0;
  if (fade === goal) return;
  fade = Math.abs(goal - fade) < 0.01 ? goal : fade + (goal - fade) * Math.min(1, dt * 8);
  for (const o of occluders) {
    o.traverse((m) => {
      if (!m.isMesh) return;
      const transparent = fade > 0 || m.userData.opacity < 1;
      // 불투명/투명은 셰이더가 달라서(OPAQUE) 바뀔 때 다시 고르게 한다. 안 하면 돌아온 뒤에도 빛 받는 모습이 달라진다.
      if (m.material.transparent !== transparent) m.material.needsUpdate = true;
      m.material.transparent = transparent;
      m.material.opacity = m.userData.opacity * (1 - 0.93 * fade);
      m.material.depthWrite = fade < 0.5;
      m.castShadow = fade < 0.5 && m.userData.shadow;
    });
  }
}

function home() {
  flyTo(TARGET.clone(), 1);
  focused = false;
  screenFocus = null;
  select(null);
  $("back").classList.remove("show");
}

// 선택한 장비의 앞면 강조: 밝은 테두리 + 옅은 덮개(블룸이 살짝 번지도록 톤 매핑을 끈다)
const outline = new THREE.Group();
outline.add(
  new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(1, 1, 1)),
    new THREE.LineBasicMaterial({ color: 0xffd9a0, toneMapped: false }),
  ),
  new THREE.Mesh(
    new THREE.BoxGeometry(1, 1, 1),
    new THREE.MeshBasicMaterial({ color: 0xffc98a, transparent: true, opacity: 0.14, depthWrite: false, toneMapped: false }),
  ),
);
outline.visible = false;
scene.add(outline);

function select(id, zoom = false) {
  selected = id;
  const u = id && units.get(id);
  outline.visible = !!u;
  if (u) {
    // 장비 몸체는 랙 안쪽 깊이 들어가 있으므로 앞쪽 얇은 상자로만 테두리를 그린다
    const box = new THREE.Box3().setFromObject(u.object);
    const front = box.max.z;
    outline.scale.set(box.max.x - box.min.x + 0.02, box.max.y - box.min.y + 0.006, 0.03);
    outline.position.set((box.min.x + box.max.x) / 2, (box.min.y + box.max.y) / 2, front - 0.01);
    if (zoom && !focused) focusRack();
  }
  if (infra) renderPanel();
}

function makeTags() {
  const holder = $("tags");
  for (const [id, u] of units) {
    if (u.info.decor || !u.info.containers?.length) continue;
    const el = document.createElement("div");
    el.className = "tag";
    el.innerHTML = `<i class="dot unknown"></i><b>${u.info.label}</b>`;
    el.onclick = () => select(selected === id ? null : id);
    holder.append(el);
    const box = new THREE.Box3().setFromObject(u.object);
    // 이름표 기준점: 장비 앞면 오른쪽 끝
    u.anchor = new THREE.Vector3(box.max.x + 0.06, (box.min.y + box.max.y) / 2, box.max.z);
    u.tag = el;
  }
}

const v = new THREE.Vector3();
const TAG_GAP = 25; // 이름표 사이 최소 간격(px). 1U 장비가 붙어 있으면 겹치므로 아래로 밀어 낸다.
function placeTags() {
  const w = stage.clientWidth, h = stage.clientHeight;
  const show = focused && !anim;
  const list = [];
  for (const u of units.values()) {
    if (!u.tag) continue;
    u.tag.classList.toggle("show", show);
    if (!show) continue;
    v.copy(u.anchor).project(camera);
    list.push({ u, x: ((v.x + 1) / 2) * w + 14, y: ((1 - v.y) / 2) * h });
  }
  list.sort((a, b) => a.y - b.y);
  // 위에서부터 겹치지 않게 내린 뒤, 전체 무게중심이 원래 위치와 같도록 다시 올린다
  const want = list.map((t) => t.y);
  for (let i = 1; i < list.length; i++) list[i].y = Math.max(list[i].y, list[i - 1].y + TAG_GAP);
  const shift = list.length ? (want.reduce((a, b) => a + b, 0) - list.reduce((a, t) => a + t.y, 0)) / list.length : 0;
  for (const t of list) {
    t.u.tag.style.left = `${t.x}px`;
    t.u.tag.style.top = `${t.y + shift}px`;
  }
}

$("back").onclick = home;
addEventListener("keydown", (e) => e.key === "Escape" && home()); // 어디를 보고 있든 방 전체로 돌아간다

// ---------------------------------------------------------------- 키보드로 카메라 움직이기
// 방향키·WASD 이동, Q/E 좌우 회전, +/- 확대. Space를 누른 채 끌면 디자인 도구처럼 화면을 옮긴다.
const PAN_KEYS = { arrowleft: [-1, 0], a: [-1, 0], arrowright: [1, 0], d: [1, 0], arrowup: [0, 1], w: [0, 1], arrowdown: [0, -1], s: [0, -1] };
const MOVE_KEYS = new Set([...Object.keys(PAN_KEYS), "q", "e", "+", "=", "-", "_"]);
const held = new Set();
let spaceHeld = false;

function setSpace(on) {
  spaceHeld = on;
  controls.mouseButtons.LEFT = on ? THREE.MOUSE.PAN : THREE.MOUSE.ROTATE;
  renderer.domElement.style.cursor = on ? "grab" : "";
}
addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if (e.code === "Space") setSpace(true);
  else if (MOVE_KEYS.has(k)) held.add(k);
  else return;
  e.preventDefault();
});
addEventListener("keyup", (e) => (e.code === "Space" ? setSpace(false) : held.delete(e.key.toLowerCase())));
addEventListener("blur", () => {
  held.clear();
  setSpace(false);
});

const sph = new THREE.Spherical();
function stepKeys(dt) {
  if (!held.size) return;
  anim = null; // 다가가는 중이면 멈추고 키를 따른다
  dt = Math.min(dt, 0.05);
  let dx = 0, dy = 0, rot = 0, zoom = 0;
  for (const k of held) {
    if (PAN_KEYS[k]) [dx, dy] = [dx + PAN_KEYS[k][0], dy + PAN_KEYS[k][1]];
    if (k === "q") rot -= 1;
    if (k === "e") rot += 1;
    if (k === "+" || k === "=") zoom += 1;
    if (k === "-" || k === "_") zoom -= 1;
  }
  // 화면 기준 초당 1.8m, 확대할수록 천천히. 방 밖으로 나가지 않게 묶는 것은 controls의 change 처리가 한다.
  const step = (1.8 * dt) / camera.zoom;
  const move = new THREE.Vector3().setFromMatrixColumn(camera.matrix, 0).multiplyScalar(dx * step)
    .addScaledVector(new THREE.Vector3().setFromMatrixColumn(camera.matrix, 1), dy * step);
  camera.position.add(move);
  controls.target.add(move);
  if (rot) {
    const off = camera.position.clone().sub(controls.target);
    sph.setFromVector3(off);
    sph.theta = THREE.MathUtils.clamp(sph.theta + rot * 1.2 * dt, controls.minAzimuthAngle, controls.maxAzimuthAngle);
    camera.position.copy(controls.target).add(off.setFromSpherical(sph));
  }
  if (zoom) {
    camera.zoom = THREE.MathUtils.clamp(camera.zoom * Math.exp(zoom * 1.5 * dt), controls.minZoom, controls.maxZoom);
    camera.updateProjectionMatrix();
  }
}

// ---------------------------------------------------------------- 조명 스위치, 고양이

// 눌러서 켜고 끄는 조명. light는 위 lamps의 순서이고, 간판은 점 조명 없이 글자만 빛난다.
const SWITCHES = [
  { node: "prop__floor_lamp", label: "스탠드", light: 0 },
  { node: "prop__desk", only: "bulb", label: "책상 스탠드", light: 1 },
  { node: "prop__table_lamp", label: "탁상등", light: 2 },
  { node: "prop__sconce", label: "벽등", light: 3 },
  { node: "prop__arc_lamp", label: "아크 스탠드", light: 4, shape: true }, // 기둥이 랙 위로 휘어 넘어가 상자로 고르면 랙 앞을 덮는다
  { node: "prop__sign", label: "HOME LAB 간판" },
];
// Blender에서 낮 테마로 내보내 빛이 꺼진 재질에 다시 줄 발광: [r, g, b, 켰을 때 세기, 껐을 때 세기]
const GLOW = {
  lamp_shade: [1.0, 0.64, 0.34, 0.5, 0],
  rattan_shade: [1.0, 0.62, 0.30, 1.8, 0],
  arc_lining: [1.0, 0.66, 0.38, 0.7, 0],
  arc_diffuser: [1.0, 0.66, 0.38, 1.0, 0],
  lamp_linen: [1.0, 0.58, 0.28, 0.12, 0],
  bulb: [1.0, 0.68, 0.40, 1.5, 0.3],
  sign_glow: [1.0, 0.72, 0.40, 2.2, 0],
};
const switches = []; // { label, light, glow: 재질[], hit: 투명 상자, on, level }

// 고르기에만 쓰는 투명 상자(그리지 않는다)
function hitBox(box, pad) {
  const size = box.getSize(new THREE.Vector3()).addScalar(pad);
  const m = new THREE.Mesh(new THREE.BoxGeometry(size.x, size.y, size.z), new THREE.MeshBasicMaterial({ visible: false }));
  box.getCenter(m.position);
  return m;
}

function setupSwitches(root) {
  for (const s of SWITCHES) {
    const node = root.getObjectByName(s.node);
    if (!node) continue;
    const glow = [];
    const zone = new THREE.Box3();
    node.traverse((o) => {
      if (!o.isMesh || !GLOW[o.material.name] || (s.only && o.material.name !== s.only)) return;
      o.material = o.material.clone(); // 같은 재질을 여러 조명이 나눠 쓰므로 따로 켜고 끄려면 복제한다
      o.material.emissive.setRGB(...GLOW[o.material.name].slice(0, 3));
      glow.push(o.material);
      zone.expandByObject(o);
    });
    if (!s.only) zone.setFromObject(node);
    // 가는 기둥이나 작은 전구도 누르기 쉽게 조금 넉넉한 투명 상자로 고른다(shape면 실제 모양으로)
    const hit = s.shape ? node : hitBox(zone, s.only ? 0.2 : 0.06);
    if (!s.shape) scene.add(hit);
    switches.push({ label: s.label, light: s.light, node, glow, hit, on: false, level: 0 });
  }
}

function stepSwitches(dt) {
  const k = Math.min(1, dt * 12);
  for (const s of switches) {
    s.level += (+s.on - s.level) * k;
    for (const m of s.glow) {
      const [, , , on, off] = GLOW[m.name];
      m.emissiveIntensity = off + (on * THEMES[theme].glow - off) * s.level;
    }
    if (s.light != null) lamps[s.light].intensity = lamps[s.light].userData.power * s.level;
    // 라탄 갓의 빛 무늬: 밤에는 또렷하게, 낮에는 햇빛에 묻혀 옅게
    for (const p of s.patterns ?? []) p.material.opacity = s.level * (theme === "night" ? 1 : 0.25);
  }
}

// 라탄 탁상등 빛 무늬. 실시간 그림자 대신, 전구에서 나간 빛이 갓의 엮은 틈(blender/textures.py rattan과 같은 격자)을
// 지나 뒤 벽과 수납장 윗면에 닿는 곳을 한 번 계산해 그림으로 깔고 더하기 혼합으로 비춘다.
const RATTAN = { around: 26, up: 13, strip: 0.30, z0: 0.032, h: 0.32, bulb: 0.16 }; // blender/props.py table_lamp와 같은 값
const rattanRadius = (t) => 0.035 + 0.065 * Math.sin(Math.PI * Math.min(t ** 0.85 * 1.02, 1)) ** 0.75 + 0.015 * (1 - t);

// 전구에서 (bx, by, bz) 방향(Blender 축, 램프 바닥 중심 기준)으로 나간 빛이 갓을 통과하면 1, 막히면 0.
function rattanPass(dx, dy, dz) {
  const { z0, h, bulb } = RATTAN;
  for (let s = 0.002; s < 0.3; s += 0.002) {
    const x = dx * s, y = dy * s, z = bulb + dz * s;
    const t = (z - z0) / h;
    if (t < 0 || t > 1) return Math.hypot(x, y) > 0.055 || z > 0 ? 1 : 0; // 위아래 입으로 나감(아래는 받침에 막힘)
    if (Math.hypot(x, y) >= rattanRadius(t)) {
      const u = (Math.atan2(y, x) / (2 * Math.PI) + 1) % 1;
      const a = (u * RATTAN.around + t * RATTAN.up) % 1, b = (((u * RATTAN.around - t * RATTAN.up) % 1) + 1) % 1;
      return Math.abs(a - 0.5) < RATTAN.strip || Math.abs(b - 0.5) < RATTAN.strip ? 0 : 1;
    }
  }
  return 1;
}

// 평면 하나(Blender 좌표의 원점 o와 두 변 ex, ey, 법선 n)에 빛 무늬 그림을 굽는다.
function rattanPattern(lamp, o, ex, ey, n, w, h) {
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const g = canvas.getContext("2d");
  const img = g.createImageData(w, h);
  for (let j = 0; j < h; j++) {
    for (let i = 0; i < w; i++) {
      const fx = (i + 0.5) / w, fy = 1 - (j + 0.5) / h;
      const px = o[0] + ex[0] * fx + ey[0] * fy, py = o[1] + ex[1] * fx + ey[1] * fy, pz = o[2] + ex[2] * fx + ey[2] * fy;
      const dx = px - lamp[0], dy = py - lamp[1], dz = pz - (lamp[2] + RATTAN.bulb);
      const d = Math.hypot(dx, dy, dz);
      const cos = Math.max(0, -(dx * n[0] + dy * n[1] + dz * n[2]) / d);
      const v = rattanPass(dx / d, dy / d, dz / d) * Math.min(1, ((0.05 / (d * d)) * cos) ** 0.7);
      const k = (j * w + i) * 4;
      img.data[k] = img.data[k + 1] = img.data[k + 2] = 255;
      img.data[k + 3] = Math.round(255 * Math.min(1, v));
    }
  }
  g.putImageData(img, 0, 0);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  const mat = new THREE.MeshBasicMaterial({ map: tex, color: 0xffb066, transparent: true, opacity: 0, blending: THREE.AdditiveBlending,
    depthWrite: false, toneMapped: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2 });
  const mesh = new THREE.Mesh(new THREE.BufferGeometry(), mat);
  // 네 모서리(Blender → three 좌표)로 평면을 만든다
  const corner = (fx, fy) => B(o[0] + ex[0] * fx + ey[0] * fy, o[1] + ex[1] * fx + ey[1] * fy, o[2] + ex[2] * fx + ey[2] * fy);
  const pts = [corner(0, 0), corner(1, 0), corner(1, 1), corner(0, 1)];
  mesh.geometry.setFromPoints([pts[0], pts[1], pts[2], pts[0], pts[2], pts[3]]);
  mesh.geometry.setAttribute("uv", new THREE.Float32BufferAttribute([0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1], 2));
  mesh.geometry.computeVertexNormals(); // 앰비언트 오클루전 패스가 법선을 읽는다
  mesh.renderOrder = 1;
  scene.add(mesh);
  return mesh;
}

function setupRattanLight(node) {
  const sw = switches.find((s) => s.glow.some((m) => m.name === "rattan_shade"));
  if (!node || !sw) return;
  const box = new THREE.Box3().setFromObject(node);
  const c = box.getCenter(new THREE.Vector3());
  const lamp = [c.x, -c.z, box.min.y]; // Blender 좌표: 램프 바닥 중심
  const wallY = 1.4 - 0.003, top = box.min.y + 0.002; // 뒤 벽 안쪽 면, 수납장 윗면
  sw.patterns = [
    rattanPattern(lamp, [lamp[0] - 0.55, wallY, top], [1.1, 0, 0], [0, 0, 0.85], [0, -1, 0], 440, 340),
    rattanPattern(lamp, [lamp[0] - 0.42, 0.97, top], [0.84, 0, 0], [0, wallY - 0.97, 0], [0, 0, 1], 420, 210),
  ];
}

// 로봇 청소기: 누르거나 가끔 저절로 충전대를 떠나 바닥 세 곳을 돌며 제자리에서 한 바퀴씩 돌고, 충전대로 후진해 들어간다.
// 청소 중에 누르면 바로 돌아간다. 자리는 가구 다리를 피해 곧게 오갈 수 있고 기본 구도에서 보이는 바닥(Blender x, y)이다.
const VAC_SPOTS = [[-0.25, -0.25], [0.10, 0.40], [-0.10, -0.75], [0.20, -0.20]].map(([x, y]) => B(x, y, 0));
const VAC_SPEED = 0.28; // m/s
const VAC_TURN = Math.PI; // rad/s
const RUG = { x0: -0.70, x1: 1.00, z0: -0.155, z1: 0.995 }; // 러그(three 좌표). 1.4cm 두께라 올라탈 때 살짝 높인다.
const rugLift = (p) => 0.014 * THREE.MathUtils.clamp((Math.min(p.x - RUG.x0, RUG.x1 - p.x, p.z - RUG.z0, RUG.z1 - p.z) + 0.08) / 0.16, 0, 1);
let vacuum = null; // { node, led, y, dock, front, heading, plan, step, next, say, bubble }

function setupVacuum(node) {
  if (!node) return;
  let led = null;
  node.traverse((o) => o.isMesh && o.material.name === "vacuum_led" && (led = o.material));
  // 노드는 바닥 중심이 원점이고 회전이 없다(blender/export.py part__). 투명 상자를 자식으로 붙여 함께 움직인다.
  const hit = hitBox(new THREE.Box3().setFromObject(node).translate(node.position.clone().negate()), 0.06);
  node.add(hit);
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  $("tags").append(bubble);
  const dock = node.position.clone();
  vacuum = { node, led, y: dock.y, dock, front: dock.clone().add(new THREE.Vector3(0, 0, 0.3)), heading: 0, plan: [], step: null, next: 45, say: null, bubble };
}

const isVacuum = (obj) => { for (let o = obj; o; o = o.parent) if (o === vacuum?.node) return true; return false; };
const vacuumBusy = () => !!vacuum && (!!vacuum.step || vacuum.plan.length > 0);
const homePlan = () => [{ kind: "face", to: vacuum.front }, { kind: "drive", to: vacuum.front }, { kind: "turn", to: 0 }, { kind: "drive", to: vacuum.dock, back: true }];

function runVacuum(t, byClick) {
  if (!vacuum) return;
  if (vacuumBusy()) {
    vacuum.plan = homePlan();
    vacuum.step = null;
    vacuum.say = { text: "충전하러 갈게요", until: t + 1.6 };
    return;
  }
  const spots = [...VAC_SPOTS].sort(() => Math.random() - 0.5).slice(0, 3);
  vacuum.plan = [{ kind: "drive", to: vacuum.front }, ...spots.flatMap((p) => [{ kind: "face", to: p }, { kind: "drive", to: p }, { kind: "spin" }]), ...homePlan()];
  if (byClick) vacuum.say = { text: "청소 시작!", until: t + 1.6 };
}

function startStep(s, t) {
  const pos = vacuum.node.position;
  s.t0 = t;
  if (s.kind === "drive") {
    s.from = pos.clone().setY(vacuum.y);
    s.dur = s.from.distanceTo(s.to) / (s.back ? VAC_SPEED / 2 : VAC_SPEED);
  } else {
    s.h0 = vacuum.heading;
    const to = s.kind === "face" ? Math.atan2(s.to.x - pos.x, s.to.z - pos.z) : s.to; // 앞(LED 쪽)은 노드의 +Z
    s.delta = s.kind === "spin" ? 2 * Math.PI : Math.atan2(Math.sin(to - s.h0), Math.cos(to - s.h0));
    s.dur = Math.abs(s.delta) / VAC_TURN;
  }
  vacuum.step = s;
}

function stepVacuum(t) {
  if (!vacuum) return;
  const { node, led } = vacuum;
  if (!vacuum.step && vacuum.plan.length) startStep(vacuum.plan.shift(), t);
  const s = vacuum.step;
  if (s) {
    const k = s.dur > 0 ? Math.min((t - s.t0) / s.dur, 1) : 1;
    const e = k * k * (3 - 2 * k);
    if (s.kind === "drive") node.position.lerpVectors(s.from, s.to, e);
    else vacuum.heading = s.h0 + s.delta * e;
    if (k === 1) {
      vacuum.step = null;
      if (!vacuum.plan.length) vacuum.next = t + 90 + Math.random() * 60;
    }
  } else if (t > vacuum.next) {
    runVacuum(t, false);
  }
  node.position.y = vacuum.y + rugLift(node.position);
  node.rotation.set(0, vacuum.heading, 0);
  // LED: 청소 중엔 파랑, 충전대에서는 초록으로 천천히 숨 쉰다
  if (led) {
    const busy = vacuumBusy();
    led.emissive.setRGB(...(busy ? [0.25, 0.6, 1.0] : [0.3, 1.0, 0.55]));
    led.emissiveIntensity = busy ? 4 : 1 + 2 * (0.5 + 0.5 * Math.sin(t * 2));
  }
  const say = vacuum.say && t < vacuum.say.until;
  vacuum.bubble.classList.toggle("show", !!say);
  if (say) {
    vacuum.bubble.textContent = vacuum.say.text;
    v.copy(node.position).setY(node.position.y + 0.22).project(camera);
    vacuum.bubble.style.left = `${((v.x + 1) / 2) * stage.clientWidth}px`;
    vacuum.bubble.style.top = `${((1 - v.y) / 2) * stage.clientHeight}px`;
  }
}

// 눌러서 움직이는 소품: 책 덮개, 안락의자 쿠션, 의자 윗부분, 스피커, 화분, 블라인드.
// 보통은 value가 target을 따라가며(빠르게 시작해 천천히 멈춘다), spring이 있으면 0으로 돌아오는 감쇠 진동을 한다.
// apply가 그 값(과 시각)으로 모양을 바꾼다.
const toys = []; // { label, pick: Object3D[], click(toy), apply(value, t), rate | spring: [강성, 감쇠], target, value, vel }
let blinds = null;
const WIN_BOTTOM = 0.80; // 창 아래 끝 높이(blender/room.py WIN)

function setupToys(root) {
  const get = (n) => root.getObjectByName(n);
  const add = (toy) => (toys.push({ target: 0, value: 0, vel: 0, ...toy }), toys.at(-1));
  const flip = (toy) => (toy.target = 1 - toy.target);

  const cover = get("part__side_table_book_b_cover");
  if (cover) {
    const hit = hitBox(new THREE.Box3().setFromObject(cover).expandByVector(new THREE.Vector3(0, 0.03, 0)), 0.05);
    scene.add(hit);
    // 덮개는 등을 축으로 넘어가 책 왼쪽(안락의자에서 볼 때)에 눕는다. 책은 blender/room.py side_table의 read_yaw(-58°)만큼 돌아 있어
    // 등 축(책의 Blender Y)도 같이 돈다: Blender (-sin a, cos a, 0) → three (-sin a, 0, -cos a)
    const yaw = THREE.MathUtils.degToRad(-58);
    const axis = new THREE.Vector3(-Math.sin(yaw), 0, -Math.cos(yaw));
    add({ label: "책", pick: [hit], rate: 5, click: flip,
      apply: (k) => cover.quaternion.setFromAxisAngle(axis, k * THREE.MathUtils.degToRad(172)) });
  }

  const pillow = get("part__armchair_pillow"), armchair = get("prop__armchair");
  if (pillow && armchair) {
    // 쿠션을 툭 누르면 납작해졌다가 몇 번 출렁이며 제 모양으로 돌아온다. 아래쪽이 좌판에 붙어 있도록 높이도 같이 낮춘다.
    const rest = pillow.position.y;
    const h = new THREE.Box3().setFromObject(pillow).getSize(new THREE.Vector3()).y;
    add({ label: "안락의자", pick: [armchair, pillow], spring: [140, 10], click: (t) => (t.vel -= 2.2),
      apply: (v) => {
        const k = Math.max(v, -0.35);
        pillow.scale.set(1 - 0.5 * k, 1 + k, 1 - 0.5 * k);
        pillow.position.y = rest + (h / 2) * k;
      } });
  }

  const top = get("part__chair_top"), base = get("prop__chair"), desk = get("prop__desk");
  if (top && base && desk) {
    // 책상에 바짝 붙어 있어 제자리에서 돌면 팔걸이·등받이가 책상을 뚫는다.
    // 사람이 하듯 책상 반대쪽으로 빼고, 한 바퀴 돌린 뒤, 다시 밀어 넣는다. 러그 위로 가면 러그 두께만큼 뜬다.
    const DUR = 2.6, PULL = 0.3; // 의자 윗부분 회전 반경 0.40m, 제자리에서 책상까지 0.34m → 0.3m 빼면 0.2m 남는다
    const rest = [base, top].map((o) => o.position.clone());
    const away = base.position.clone().sub(new THREE.Box3().setFromObject(desk).getCenter(new THREE.Vector3())).setY(0).normalize();
    const ease = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : x < 0.5 ? 2 * x * x : 1 - (-2 * x + 2) ** 2 / 2);
    const p = new THREE.Vector3();
    let t0 = null; // 도는 중이면 시작 시각
    add({ label: "의자", pick: [base, top], rate: 0,
      click: () => (t0 ??= clock.getElapsedTime()), // 도는 중에 누르면 무시
      apply: (_, t) => {
        if (t0 === null) return;
        const s = Math.min((t - t0) / DUR, 1);
        if (s === 1) t0 = null; // 프레임이 띄엄띄엄 와도 마지막엔 꼭 제자리(s = 1)를 한 번 그린다
        const out = PULL * (s < 0.5 ? ease(s / 0.25) : ease((1 - s) / 0.25)); // 앞 1/4에 빼고 뒤 1/4에 넣는다
        top.rotation.y = 2 * Math.PI * ease((s - 0.2) / 0.6);
        [base, top].forEach((o, i) => {
          p.copy(rest[i]).addScaledVector(away, out);
          o.position.set(p.x, rest[i].y + rugLift(p), p.z);
        });
      } });
  }

  const speaker = get("part__speaker");
  if (speaker) {
    // 음악이 흐르는 셈 치고 120bpm 박자에 맞춰 통이 들썩이고 음표가 떠오른다. 소리는 내지 않는다.
    let nextNote = 0;
    add({ label: "스피커", pick: [speaker], rate: 6, click: flip,
      apply: (k, t) => {
        const beat = k * Math.max(0, Math.sin(t * Math.PI * 4)) ** 4;
        speaker.scale.set(1 + 0.012 * beat, 1 + 0.035 * beat, 1 + 0.012 * beat);
        if (k > 0.5 && t > nextNote) {
          floatNote(speaker);
          nextNote = t + 0.45 + Math.random() * 0.35;
        }
      } });
  }

  // 책장 책: 누르면 등 쪽(방 안, +X)으로 살짝 빠져나왔다가 제자리로 미끄러져 들어간다(임계 감쇠라 튕기지 않는다)
  for (const o of root.children) {
    if (!/^part__shelf_\w+_book_\d+$/.test(o.name)) continue;
    const rest = o.position.x;
    add({ label: "책", pick: [o], spring: [9, 6], click: (t) => (t.vel = 8), apply: (k) => (o.position.x = rest + 0.07 * Math.max(k, 0)) });
  }

  // 화분: 누르면 바닥을 축으로 살짝 흔들리다 멈춘다. 흔들리는 방향은 화분마다 다르다.
  for (const o of root.children) {
    if (!o.name.startsWith("part__") || !o.name.includes("plant")) continue;
    const a = Math.random() * Math.PI * 2;
    add({ label: "화분", pick: [o], spring: [55, 3.5], click: (t) => (t.vel += 2.5),
      apply: (k) => o.rotation.set(0.12 * k * Math.cos(a), 0, 0.12 * k * Math.sin(a)) });
  }

  const slats = [];
  for (let i = 0, o; (o = get(`part__blind_${String(i).padStart(2, "0")}`)); i++) slats.push(o);
  const bar = get("part__blind_bottom");
  if (slats.length && bar) {
    // 걷어 올린 자리(GLB)에서 창턱 바로 위까지 같은 간격으로 내리고, 살을 기울여 빛을 가린다
    const parts = [...slats, bar];
    const up = parts.map((o) => o.position.y);
    const gap = (up[0] - (WIN_BOTTOM + 0.05)) / slats.length;
    const down = up.map((y, i) => up[0] - i * gap);
    const hit = hitBox(new THREE.Box3().setFromPoints([B(-1.38, 1.33, WIN_BOTTOM), B(-0.32, 1.40, 2.08)]), 0);
    scene.add(hit);
    blinds = add({ label: "블라인드", pick: [hit], rate: 3, click: flip,
      apply: (k) => parts.forEach((o, i) => {
        o.position.y = up[i] + (down[i] - up[i]) * k;
        if (o !== bar) o.rotation.x = k * 1.05;
      }) });
  }
}

function floatNote(obj) {
  const box = new THREE.Box3().setFromObject(obj);
  v.set((box.min.x + box.max.x) / 2, box.max.y + 0.02, (box.min.z + box.max.z) / 2).project(camera);
  const el = document.createElement("div");
  el.className = "music";
  el.textContent = Math.random() < 0.5 ? "♪" : "♫";
  el.style.left = `${((v.x + 1) / 2) * stage.clientWidth}px`;
  el.style.top = `${((1 - v.y) / 2) * stage.clientHeight}px`;
  el.style.setProperty("--dx", `${Math.round((Math.random() - 0.5) * 40)}px`);
  el.onanimationend = () => el.remove();
  $("tags").append(el);
}

function stepToys(dt, t) {
  dt = Math.min(dt, 0.1); // 탭을 오래 비웠다 돌아와도 튀지 않게
  for (const toy of toys) {
    if (toy.spring) {
      const [stiff, damp] = toy.spring;
      for (let i = 0, n = Math.ceil(dt / 0.005); i < n; i++) {
        toy.vel += (-stiff * toy.value - damp * toy.vel) * (dt / n);
        toy.value += toy.vel * (dt / n);
      }
    } else {
      toy.value += (toy.target - toy.value) * Math.min(1, dt * toy.rate);
    }
    toy.apply(toy.value, t);
  }
  // 블라인드를 내리면 창으로 드는 빛이 줄어든다
  windowLight.intensity = THEMES[theme].window * (1 - 0.75 * (blinds?.value ?? 0));
}

const toyOf = (hit) => {
  for (let o = hit?.object; o; o = o.parent) {
    const toy = toys.find((t) => t.pick.includes(o));
    if (toy) return toy;
  }
  return null;
};

// ---------------------------------------------------------------- 상태

function paintLeds() {
  for (const [id, led] of leds) {
    led.status = containerStatus(status, id);
    led.mesh.material.emissive.setRGB(...STATUS_COLOR[led.status]);
  }
  const unseen = infra.units.flatMap((u) => (u.containers ?? []).map((c) => c.id)).filter((id) => !leds.has(id));
  if (unseen.length) console.warn("GLB에 LED가 없는 컨테이너:", unseen);
  renderPanel();
}

async function refreshHistory() {
  history = await fetchHistory();
  paintMonitor();
  $("charts-src").textContent = !history?.start ? "" : history.demo ? "예시 데이터" : "1분 간격";
  $("chart-list").innerHTML = chartsHTML(history);
}

async function refreshGithub() {
  github = await fetchGithub();
  paintDesk();
  $("commits-src").textContent = !github?.commits?.length ? "" : github.demo ? "예시 데이터" : "공개 저장소";
  $("commit-list").innerHTML = commitsHTML(github);
}

async function refresh() {
  try {
    status = await fetchStatus(infra);
  } catch (e) {
    console.error(e);
    status = null; // 실패하면 전부 데이터 없음
  }
  paintLeds();
}

// ---------------------------------------------------------------- 포인터: 호버 툴팁, 클릭 확대

const tip = $("tip");
const ray = new THREE.Raycaster();
const pointer = new THREE.Vector2();

function pick(e, objects) {
  const r = renderer.domElement.getBoundingClientRect();
  pointer.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(pointer, camera);
  return ray.intersectObjects(objects, true)[0];
}

function unitOf(obj) {
  for (let o = obj; o; o = o.parent) {
    const [kind, id] = o.name.split("__");
    if (kind === "unit") return units.get(id);
  }
  return null;
}

const inRack = (obj) => { for (let o = obj; o; o = o.parent) if (o === rack) return true; return false; };
// 랙 확대 중에는 비켜 준(반투명) 소품을 누를 수 없게 해 그 뒤의 장비가 눌리게 한다
const pickables = () => [rack, ...(monitor?.parts ?? []), ...(desk?.parts ?? []), ...switches.filter((s) => !(focused && inOccluder(s.node))).map((s) => s.hit),
  ...toys.flatMap((t) => t.pick).filter((o) => !(focused && inOccluder(o))), vacuum?.node].filter(Boolean);
const switchOf = (hit) => hit && switches.find((s) => { for (let o = hit.object; o; o = o.parent) if (o === s.hit) return true; return false; });
const onParts = (hit, s) => !!hit && !!s && s.parts.some((p) => { for (let o = hit.object; o; o = o.parent) if (o === p) return true; return false; });
const onMonitor = (hit) => onParts(hit, monitor);
const onDesk = (hit) => onParts(hit, desk);

function showTip(e, html) {
  tip.innerHTML = html;
  tip.style.display = "block";
  tip.style.left = `${Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 8)}px`;
  tip.style.top = `${Math.min(e.clientY + 14, innerHeight - tip.offsetHeight - 8)}px`;
}

renderer.domElement.addEventListener("pointermove", (e) => {
  if (!infra || !rack || e.buttons) return (tip.style.display = "none");
  const hit = pick(e, pickables());
  renderer.domElement.style.cursor = spaceHeld ? "grab" : hit ? "pointer" : "";
  // 소품은 이름표 없이 눌렀을 때 움직이는 것으로 충분하다(손가락 커서만 바꾼다)
  if (switchOf(hit) || toyOf(hit) || (hit && isVacuum(hit.object))) return (tip.style.display = "none");
  if (onMonitor(hit)) return showTip(e, "<b>Grafana Cloud</b><div class=\"row muted\">최근 1시간 서버 지표 · 눌러서 크게 보기</div>");
  if (onDesk(hit)) return showTip(e, "<b>GitHub</b><div class=\"row muted\">최근 공개 커밋 · 눌러서 크게 보기</div>");
  const unit = hit && unitOf(hit.object);
  if (!unit || unit.info.decor || !unit.info.containers?.length) return (tip.style.display = "none");
  const { info } = unit;
  const rows = info.containers.map((c) => {
    const s = containerStatus(status, c.id);
    return `<div class="row"><i class="dot ${s}"></i>${c.name} <span class="muted">${STATUS_LABEL[s]}</span></div>`;
  });
  const us = unitStatus(status, info);
  showTip(e, `<b>${info.label}${us ? ` <i class="dot ${us}"></i>` : ""}</b>${rows.join("")}`);
});
renderer.domElement.addEventListener("pointerleave", () => (tip.style.display = "none"));

// 드래그(회전·이동)와 구분해 짧게 누른 것만 클릭으로 본다
let down = null;
renderer.domElement.addEventListener("pointerdown", (e) => (down = [e.clientX, e.clientY]));
renderer.domElement.addEventListener("pointerup", (e) => {
  if (!down || spaceHeld || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 6 || !rack) return;
  const hit = pick(e, pickables());
  const sw = switchOf(hit);
  if (sw) {
    sw.on = !sw.on;
    tip.style.display = "none";
  } else if (toyOf(hit)) {
    toyOf(hit).click(toyOf(hit));
    tip.style.display = "none";
  } else if (hit && isVacuum(hit.object)) {
    runVacuum(clock.getElapsedTime(), true);
    tip.style.display = "none";
  } else if (onMonitor(hit)) {
    if (screenFocus !== "grafana") focusScreen("grafana");
  } else if (onDesk(hit)) {
    if (screenFocus !== "desk") focusScreen("desk");
  } else if (hit) {
    const unit = unitOf(hit.object);
    if (!focused) focusRack();
    select(unit && !unit.info.decor && unit.info.containers?.length ? unit.info.id : null);
  } else if (focused || screenFocus) {
    home();
  }
});

// ---------------------------------------------------------------- 시작

let lastT = 0;
renderer.setAnimationLoop(() => {
  const t = clock.getElapsedTime();
  stepSwitches(t - lastT);
  stepFade(t - lastT);
  stepToys(t - lastT, t);
  stepVacuum(t);
  const base = THEMES[theme].led;
  for (const led of leds.values()) {
    // 오류는 깜박이고, 데이터 없음은 꺼진 것처럼 어둡게 둔다.
    const k = led.status === "error" ? 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * 6))
      : led.status === "unknown" ? 0.12 : 1;
    led.mesh.material.emissiveIntensity = base * k;
  }
  stepKeys(t - lastT);
  stepAnim(t);
  lastT = t;
  controls.update();
  placeTags();
  composer.render();
});

infra = await (await fetch("data/infra.json", { cache: "no-cache" })).json();
$("title").textContent = infra.host.title;
$("subtitle").textContent = infra.host.subtitle;
// Blender 내보내기는 Draco로 압축한다(blender/export.py).
const draco = new DRACOLoader().setDecoderPath("https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/draco/gltf/");
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).setDRACOLoader(draco);
const [gltf, nightSky] = await Promise.all([
  loader.loadAsync("data/scene.glb"),
  new THREE.TextureLoader().loadAsync("data/textures/skyline_night.png"),
]);
setupScene(gltf, nightSky);
applyTheme(clockTheme());
setInterval(() => {
  if (autoTheme && clockTheme() !== theme) applyTheme(clockTheme());
}, 60_000);
renderPanel();
refreshHistory();
setInterval(refreshHistory, HISTORY_MS);
refreshGithub();
setInterval(refreshGithub, GITHUB_MS);
await refresh();
setInterval(refresh, REFRESH_MS);
