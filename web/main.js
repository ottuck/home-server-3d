import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { STATUS_COLOR, fetchStatus, containerStatus, unitStatus } from "./status.js";

const REFRESH_MS = 5000;
const STATUS_LABEL = { ok: "정상", warn: "주의", error: "오류", unknown: "데이터 없음" };
const RANK = { ok: 0, unknown: 1, warn: 2, error: 3 };

// Blender 좌표 (x, y, z) -> glTF/three 좌표 (x, z, -y)
const B = (x, y, z) => new THREE.Vector3(x, z, -y);

// Blender 방 카메라(build_room.py)와 같은 구도: tilt 58°, yaw 40°, 목표점 (0, 0.1, 1.08), 화면 6.5 × 4.06m.
const TARGET = B(0, 0.1, 1.08);
const TILT = THREE.MathUtils.degToRad(58);
const YAW = THREE.MathUtils.degToRad(40);
const VIEW_DIR = new THREE.Vector3(Math.sin(TILT) * Math.sin(YAW), Math.cos(TILT), Math.sin(TILT) * Math.cos(YAW));
const VIEW_HALF_W = 6.5 / 2;
const VIEW_HALF_H = 4.06 / 2;
// 방 바닥 범위(팬 제한): Blender x[-1.7,1.7], y[-1.4,1.4]
const PAN_MIN = B(-1.7, 1.4, 0.3), PAN_MAX = B(1.7, -1.4, 1.8);

// blender/room.py THEMES의 조명을 three.js 조명으로 옮긴 값. 강도는 눈으로 맞췄다.
const THEMES = {
  day: {
    bg: 0xeee8df, hemi: 1.5, sun: 3.0, env: 0.6, window: 1.2, lamps: 0, rack: 0,
    shade: 0, bulb: 0.3, sign: 0, screen: 0.7, led: 7, bloom: [0.25, 0.3, 2.2],
  },
  night: {
    bg: 0x1a2340, hemi: 0.10, sun: 0, env: 0.05, window: 0.6, lamps: 1, rack: 1.2,
    shade: 0.75, bulb: 2.2, sign: 2.2, screen: 1.0, led: 14, bloom: [0.45, 0.3, 1.0],
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
const warm = 0xffb873;
const lamps = [
  [B(-1.36, -1.08, 1.42), 3.6, 6.5, true], // 스탠드: 방 전체를 밝히는 주 조명
  [B(-1.25, 0.66, 1.08), 0.7, 2.5, false],
  [B(0.80, 1.20, 0.76), 0.9, 3.0, false],
  [B(-0.13, 1.31, 1.74), 0.9, 3.0, false],
].map(([pos, power, dist, shadow]) => {
  const l = new THREE.PointLight(warm, 0, dist, 1.6);
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
let rack = null;
let infra = null;
let status = null;
globalThis.viewer = { leds, units, mats, scene, camera, get status() { return status; } }; // 콘솔 디버깅용

function setupScene(gltf, nightSky) {
  const root = gltf.scene;
  root.traverse((o) => {
    if (o.isMesh) {
      const glow = o.name.endsWith("_screen") || o.name === "skyline";
      // 조명 기구는 자기 빛을 가리지 않도록 그림자를 만들지 않는다
      const fixture = ["prop__floor_lamp", "prop__table_lamp", "prop__sconce"].includes(o.name);
      o.castShadow = !glow && !fixture;
      o.receiveShadow = !glow;
      for (const m of [o.material].flat()) {
        mats.set(m.name, m);
        // Blender 코트는 glTF에서 거울처럼 매끈해져 점 조명이 바닥에 점으로 맺힌다.
        // 바닥은 은은한 광택을 남기고(Cycles 렌더의 느낌), 나머지는 더 거칠게 한다.
        if (m.clearcoat) m.clearcoatRoughness = Math.max(m.clearcoatRoughness, m.name === "floor_wood" ? 0.22 : 0.4);
      }
      if (o.name.endsWith("_screen")) screens.push(o.material);
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
  scene.add(root);
  root.updateMatrixWorld(true); // 첫 렌더 전에 장비 위치(이름표 기준점)를 계산하려면 필요하다
  makeTags();
}

// ---------------------------------------------------------------- 테마

const GLOW = {
  // Blender에서 낮 테마로 내보내 빛이 꺼진 재질은 여기서 색을 다시 준다
  lamp_shade: [1.0, 0.78, 0.50, "shade"],
  bulb: [1.0, 0.80, 0.55, "bulb"],
  sign_glow: [1.0, 0.72, 0.40, "sign"],
};

let theme = "day";
function applyTheme(name) {
  theme = name;
  const t = THEMES[name];
  document.body.classList.toggle("night", name === "night");
  document.getElementById("theme").textContent = name === "day" ? "밤" : "낮";
  scene.background = new THREE.Color(t.bg);
  hemi.intensity = t.hemi;
  sun.intensity = t.sun;
  sun.castShadow = t.sun > 0;
  scene.environmentIntensity = t.env;
  windowLight.intensity = t.window;
  windowLight.color.set(name === "day" ? 0xfff0d8 : 0x8ea4ff);
  for (const l of lamps) l.intensity = l.userData.power * t.lamps;
  rackLight.intensity = t.rack;
  for (const [mat, [r, g, b, key]] of Object.entries(GLOW)) {
    const m = mats.get(mat);
    if (!m) continue;
    m.emissive.setRGB(r, g, b);
    m.emissiveIntensity = t[key];
  }
  for (const m of screens) m.emissiveIntensity = t.screen;
  if (skyline) {
    const tex = name === "day" ? skyline.day : skyline.night;
    skyline.material.map = skyline.material.emissiveMap = tex;
    skyline.material.needsUpdate = true;
  }
  [bloom.strength, bloom.radius, bloom.threshold] = t.bloom;
}
document.getElementById("theme").onclick = () => applyTheme(theme === "day" ? "night" : "day");

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
$("services").addEventListener("click", (e) => {
  const li = e.target.closest(".svc");
  if (li) select(li.dataset.id === selected ? null : li.dataset.id, true);
});

// ---------------------------------------------------------------- 랙 확대·선택

let focused = false;
let selected = null;
let anim = null;
const clock = new THREE.Clock();

function flyTo(target, zoom) {
  anim = {
    t0: clock.getElapsedTime(),
    from: { target: controls.target.clone(), position: camera.position.clone(), zoom: camera.zoom },
    to: { target, position: target.clone().addScaledVector(VIEW_DIR, 12), zoom },
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
  $("back").classList.add("show");
}

function home() {
  flyTo(TARGET.clone(), 1);
  focused = false;
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
addEventListener("keydown", (e) => e.key === "Escape" && focused && home());

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

renderer.domElement.addEventListener("pointermove", (e) => {
  if (!infra || !rack || e.buttons) return (tip.style.display = "none");
  const hit = pick(e, [rack]);
  renderer.domElement.style.cursor = hit ? "pointer" : "";
  const unit = hit && unitOf(hit.object);
  if (!unit || unit.info.decor || !unit.info.containers?.length) return (tip.style.display = "none");
  const { info } = unit;
  const rows = info.containers.map((c) => {
    const s = containerStatus(status, c.id);
    return `<div class="row"><i class="dot ${s}"></i>${c.name} <span class="muted">${STATUS_LABEL[s]}</span></div>`;
  });
  const us = unitStatus(status, info);
  tip.innerHTML = `<b>${info.label}${us ? ` <i class="dot ${us}"></i>` : ""}</b>${rows.join("")}`;
  tip.style.display = "block";
  tip.style.left = `${Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 8)}px`;
  tip.style.top = `${Math.min(e.clientY + 14, innerHeight - tip.offsetHeight - 8)}px`;
});
renderer.domElement.addEventListener("pointerleave", () => (tip.style.display = "none"));

// 드래그(회전·이동)와 구분해 짧게 누른 것만 클릭으로 본다
let down = null;
renderer.domElement.addEventListener("pointerdown", (e) => (down = [e.clientX, e.clientY]));
renderer.domElement.addEventListener("pointerup", (e) => {
  if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 6 || !rack) return;
  const hit = pick(e, [rack]);
  if (hit) {
    const unit = unitOf(hit.object);
    if (!focused) focusRack();
    select(unit && !unit.info.decor && unit.info.containers?.length ? unit.info.id : null);
  } else if (focused) {
    home();
  }
});

// ---------------------------------------------------------------- 시작

renderer.setAnimationLoop(() => {
  const t = clock.getElapsedTime();
  const base = THEMES[theme].led;
  for (const led of leds.values()) {
    // 오류는 깜박이고, 데이터 없음은 꺼진 것처럼 어둡게 둔다.
    const k = led.status === "error" ? 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * 6))
      : led.status === "unknown" ? 0.12 : 1;
    led.mesh.material.emissiveIntensity = base * k;
  }
  stepAnim(t);
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
applyTheme(matchMedia("(prefers-color-scheme: dark)").matches ? "night" : "day");
renderPanel();
await refresh();
setInterval(refresh, REFRESH_MS);
