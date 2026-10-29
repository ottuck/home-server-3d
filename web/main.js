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

// Blender 좌표 (x, y, z) -> glTF/three 좌표 (x, z, -y)
const B = (x, y, z) => new THREE.Vector3(x, z, -y);

// Blender 방 카메라(build_room.py)와 같은 구도: tilt 58°, yaw 40°, 목표점 (0, 0.1, 1.08), 화면 6.5 × 4.06m.
const TARGET = B(0, 0.1, 1.08);
const TILT = THREE.MathUtils.degToRad(58);
const YAW = THREE.MathUtils.degToRad(40);
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

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.AgXToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;

const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 40);
camera.position.copy(TARGET).add(
  new THREE.Vector3(Math.sin(TILT) * Math.sin(YAW), Math.cos(TILT), Math.sin(TILT) * Math.cos(YAW)).multiplyScalar(12),
);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.copy(TARGET);
controls.enableDamping = true;
controls.screenSpacePanning = true;
controls.minAzimuthAngle = YAW - THREE.MathUtils.degToRad(25);
controls.maxAzimuthAngle = YAW + THREE.MathUtils.degToRad(25);
controls.minPolarAngle = TILT - THREE.MathUtils.degToRad(14);
controls.maxPolarAngle = TILT + THREE.MathUtils.degToRad(10);
controls.minZoom = 0.9;
controls.maxZoom = 4;
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
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.4, 0.4, 0.9);
composer.addPass(bloom);
composer.addPass(new OutputPass());

function resize() {
  // 방 전체(6.5 × 4.06m)가 가로·세로 어느 화면에도 들어오게 맞춘다
  const a = innerWidth / innerHeight;
  const fitW = a < VIEW_HALF_W / VIEW_HALF_H;
  const tight = VIEW_HALF_W * 0.84; // 세로 화면은 좌우 여백을 줄여 방을 크게 보인다
  const hw = fitW ? tight : VIEW_HALF_H * a;
  const hh = fitW ? tight / a : VIEW_HALF_H;
  Object.assign(camera, { left: -hw, right: hw, top: hh, bottom: -hh });
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  composer.setSize(innerWidth, innerHeight);
}
addEventListener("resize", resize);
resize();

// ---------------------------------------------------------------- 장면

const leds = new Map(); // container -> { mesh, status }
const units = new Map(); // unit id -> { object, info }
const mats = new Map(); // 재질 이름 -> 재질(GLB 안에서 공유)
const screens = []; // 화면 재질(*_screen)
let skyline = null; // { material, day, night }
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

// ---------------------------------------------------------------- 상태

function paintLeds() {
  for (const [name, led] of leds) {
    led.status = containerStatus(status, name);
    led.mesh.material.emissive.setRGB(...STATUS_COLOR[led.status]);
  }
  const unseen = infra.units.flatMap((u) => u.containers ?? []).filter((c) => !leds.has(c));
  if (unseen.length) console.warn("GLB에 LED가 없는 컨테이너:", unseen);
  document.getElementById("updated").textContent =
    `가짜 상태 · ${new Date(status.updatedAt).toLocaleTimeString("ko-KR")}`;
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

// ---------------------------------------------------------------- 호버 툴팁

const tip = document.getElementById("tip");
const ray = new THREE.Raycaster();
const pointer = new THREE.Vector2();

function unitOf(obj) {
  for (let o = obj; o; o = o.parent) {
    const [kind, id] = o.name.split("__");
    if (kind === "unit") return units.get(id);
  }
  return null;
}

renderer.domElement.addEventListener("pointermove", (e) => {
  if (!infra || e.buttons) return (tip.style.display = "none");
  pointer.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  ray.setFromCamera(pointer, camera);
  const hit = ray.intersectObjects([...units.values()].map((u) => u.object), true)[0];
  const unit = hit && unitOf(hit.object);
  if (!unit || unit.info.decor) return (tip.style.display = "none");
  const { info } = unit;
  const rows = (info.containers ?? []).map((c) => {
    const s = containerStatus(status, c);
    return `<div class="row"><i class="dot ${s}"></i>${c} <span class="muted">${STATUS_LABEL[s]}</span></div>`;
  });
  const us = unitStatus(status, info);
  tip.innerHTML = `<b>${info.label ?? info.id}${us ? ` <i class="dot ${us}"></i>` : ""}</b>` +
    (rows.join("") || `<div class="muted">컨테이너 없음</div>`);
  tip.style.display = "block";
  tip.style.left = `${Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 8)}px`;
  tip.style.top = `${Math.min(e.clientY + 14, innerHeight - tip.offsetHeight - 8)}px`;
});

// ---------------------------------------------------------------- 시작

const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const t = clock.getElapsedTime();
  const base = THEMES[theme].led;
  for (const led of leds.values()) {
    // 오류는 깜박이고, 데이터 없음은 꺼진 것처럼 어둡게 둔다.
    const k = led.status === "error" ? 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * 6))
      : led.status === "unknown" ? 0.12 : 1;
    led.mesh.material.emissiveIntensity = base * k;
  }
  controls.update();
  composer.render();
});

infra = await (await fetch("data/infra.json", { cache: "no-cache" })).json();
document.getElementById("title").textContent = infra.host.title;
document.getElementById("subtitle").textContent = infra.host.subtitle;
// Blender 내보내기는 Draco로 압축한다(blender/export.py).
const draco = new DRACOLoader().setDecoderPath("https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/draco/gltf/");
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).setDRACOLoader(draco);
const [gltf, nightSky] = await Promise.all([
  loader.loadAsync("data/scene.glb"),
  new THREE.TextureLoader().loadAsync("data/textures/skyline_night.png"),
]);
setupScene(gltf, nightSky);
applyTheme(matchMedia("(prefers-color-scheme: dark)").matches ? "night" : "day");
await refresh();
setInterval(refresh, REFRESH_MS);
