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

// Blender 카메라(stage.camera)와 같은 구도: tilt 58°, yaw 34°, ortho_scale 2.1, 목표점 높이 0.72m.
// Blender (x, y, z) -> glTF (x, z, -y)
const TARGET = new THREE.Vector3(0, 0.72, 0);
const TILT = THREE.MathUtils.degToRad(58);
const YAW = THREE.MathUtils.degToRad(34);
const ORTHO_HALF = 2.1 / 2;

const THEMES = {
  day: {
    bg: 0xefe9e1, wall: 0xf1ebe3, floor: 1.0,
    hemi: 1.7, sun: 3.4, env: 0.8, lamp: 0, front: 0,
    led: 7, bloom: [0.3, 0.3, 2.5],
  },
  night: {
    bg: 0x15151b, wall: 0x5d5a63, floor: 0.45,
    hemi: 0.12, sun: 0.0, env: 0.08, lamp: 2.2, front: 1.4,
    led: 14, bloom: [0.55, 0.25, 1.6],
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

const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 30);
camera.position.copy(TARGET).add(
  new THREE.Vector3(Math.sin(TILT) * Math.sin(YAW), Math.cos(TILT), Math.sin(TILT) * Math.cos(YAW)).multiplyScalar(8),
);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.copy(TARGET);
controls.enablePan = false;
controls.enableDamping = true;
controls.minAzimuthAngle = YAW - THREE.MathUtils.degToRad(22);
controls.maxAzimuthAngle = YAW + THREE.MathUtils.degToRad(22);
controls.minPolarAngle = TILT - THREE.MathUtils.degToRad(14);
controls.maxPolarAngle = TILT + THREE.MathUtils.degToRad(10);
controls.minZoom = 0.85;
controls.maxZoom = 3;
controls.update();

// ---------------------------------------------------------------- 조명

const hemi = new THREE.HemisphereLight(0xfff6ea, 0xd9b38c, 1);
const sun = new THREE.DirectionalLight(0xfff1de, 1);
sun.position.set(-1.6, 3.2, 2.4);
sun.target.position.copy(TARGET);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = sun.shadow.camera.bottom = -2;
sun.shadow.camera.right = sun.shadow.camera.top = 2;
sun.shadow.radius = 6;
sun.shadow.bias = -0.0005;
// 밤: 따뜻한 벽등 + 랙 앞 윗프레임 아래 숨은 조명
const lamp = new THREE.PointLight(0xffb36b, 1, 4, 1.6);
lamp.position.set(-0.7, 1.65, -0.55);
const front = new THREE.SpotLight(0xdfe8ff, 1, 3, THREE.MathUtils.degToRad(50), 0.8, 1.5);
front.position.set(0, 1.3, 0.55);
front.target.position.set(0, 0.5, 0.25);
scene.add(hemi, sun, sun.target, lamp, front, front.target);

// ---------------------------------------------------------------- 방(임시: 바닥 + 벽 두 장)

function woodTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 1024;
  const g = c.getContext("2d");
  const rows = 8, plank = 1024 / rows;
  for (let r = 0; r < rows; r++) {
    let x = -((r * 397) % 600);
    while (x < 1024) {
      const w = 420 + ((x * 13 + r * 71) % 260);
      const l = 72 + ((x + r * 31) % 9);
      g.fillStyle = `hsl(28, 46%, ${l}%)`;
      g.fillRect(x, r * plank, w, plank);
      g.fillStyle = "rgba(120, 70, 30, 0.25)";
      g.fillRect(x, r * plank, 2, plank);
      x += w;
    }
    g.fillStyle = "rgba(120, 70, 30, 0.3)";
    g.fillRect(0, r * plank, 1024, 2);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(2.5, 2.5);
  t.anisotropy = 8;
  return t;
}

const floorMat = new THREE.MeshStandardMaterial({ map: woodTexture(), roughness: 0.7 });
const wallMat = new THREE.MeshStandardMaterial({ color: 0xf1ebe3, roughness: 0.95 });
const skirtMat = new THREE.MeshStandardMaterial({ color: 0xe6c4a0, roughness: 0.6 });
const room = new THREE.Group();
scene.add(room);

function buildRoom(box) {
  const back = box.min.z - 0.35, left = box.min.x - 0.75, size = 6, h = 3;
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(size, size), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(left + size / 2, 0, back + size / 2);
  floor.receiveShadow = true;
  const wallB = new THREE.Mesh(new THREE.PlaneGeometry(size, h), wallMat);
  wallB.position.set(left + size / 2, h / 2, back);
  wallB.receiveShadow = true;
  const wallL = new THREE.Mesh(new THREE.PlaneGeometry(size, h), wallMat);
  wallL.rotation.y = Math.PI / 2;
  wallL.position.set(left, h / 2, back + size / 2);
  wallL.receiveShadow = true;
  const skirtB = new THREE.Mesh(new THREE.BoxGeometry(size, 0.08, 0.015), skirtMat);
  skirtB.position.set(left + size / 2, 0.04, back + 0.0075);
  const skirtL = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.08, size), skirtMat);
  skirtL.position.set(left + 0.0075, 0.04, back + size / 2);
  room.add(floor, wallB, wallL, skirtB, skirtL);
}

// ---------------------------------------------------------------- 렌더 파이프라인

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.4, 0.4, 0.9);
composer.addPass(bloom);
composer.addPass(new OutputPass());

function resize() {
  const a = innerWidth / innerHeight;
  const hw = a >= 1 ? ORTHO_HALF * a : ORTHO_HALF;
  const hh = a >= 1 ? ORTHO_HALF : ORTHO_HALF / a;
  Object.assign(camera, { left: -hw, right: hw, top: hh, bottom: -hh });
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  composer.setSize(innerWidth, innerHeight);
}
addEventListener("resize", resize);
resize();

// ---------------------------------------------------------------- 테마

let theme = "day";
function applyTheme(name) {
  theme = name;
  const t = THEMES[name];
  document.body.classList.toggle("night", name === "night");
  document.getElementById("theme").textContent = name === "day" ? "밤" : "낮";
  scene.background = new THREE.Color(t.bg);
  wallMat.color.set(t.wall);
  floorMat.color.setScalar(t.floor);
  hemi.intensity = t.hemi;
  sun.intensity = t.sun;
  scene.environmentIntensity = t.env;
  lamp.intensity = t.lamp;
  front.intensity = t.front;
  [bloom.strength, bloom.radius, bloom.threshold] = t.bloom;
}
document.getElementById("theme").onclick = () => applyTheme(theme === "day" ? "night" : "day");
applyTheme(matchMedia("(prefers-color-scheme: dark)").matches ? "night" : "day");

// ---------------------------------------------------------------- 랙 + LED

const leds = new Map(); // container -> { mesh, status }
const units = new Map(); // unit id -> { object, info }
let infra = null;
let status = null;
globalThis.viewer = { leds, units, get status() { return status; } }; // 콘솔 디버깅용

function setupRack(gltf) {
  const rack = gltf.scene;
  rack.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
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
  scene.add(rack);
  buildRoom(new THREE.Box3().setFromObject(rack));
}

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

infra = await (await fetch("data/infra.json")).json();
document.getElementById("title").textContent = infra.host.title;
document.getElementById("subtitle").textContent = infra.host.subtitle;
// Blender 내보내기는 Draco로 압축한다(blender/export.py).
const draco = new DRACOLoader().setDecoderPath("https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/draco/gltf/");
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).setDRACOLoader(draco);
setupRack(await loader.loadAsync("data/rack.glb"));
await refresh();
setInterval(refresh, REFRESH_MS);
