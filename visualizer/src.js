import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import RAPIER from '@dimforge/rapier3d-compat';
import GUI from 'lil-gui';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import './style.css';
import config from './scenes/incline.json';

if (config.scene !== 'inclined-plane') throw new Error(`Unsupported scene type: ${config.scene}`);
const app=document.querySelector('#app');
app.innerHTML=`<main id="viewport"><div class="hint">Drag to orbit • Scroll to zoom • Right-drag to pan</div></main><aside id="side"><h1 id="title"></h1><p id="description"></p><div><button id="pause">Pause</button><button id="reset">Reset</button><button id="highlight">Toggle highlight</button><button id="forces">Toggle force arrows</button></div><div id="readout"></div><div id="equation"></div><div class="gui-container" id="gui"></div></aside>`;
document.querySelector('#title').textContent=config.title;
document.querySelector('#description').textContent=config.description;

await RAPIER.init();
const viewport=document.querySelector('#viewport');
const scene=new THREE.Scene();scene.background=new THREE.Color('#0f172a');
const camera=new THREE.PerspectiveCamera(45,1,0.1,100);camera.position.set(8,6,10);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));viewport.prepend(renderer.domElement);
const labels=new CSS2DRenderer();labels.domElement.style.position='absolute';labels.domElement.style.top='0';labels.domElement.style.left='0';labels.domElement.style.pointerEvents='none';viewport.appendChild(labels.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,0.8,0);controls.enableDamping=true;controls.update();
scene.add(new THREE.AmbientLight(0xffffff,1.5));const sun=new THREE.DirectionalLight(0xffffff,2.5);sun.position.set(4,9,6);scene.add(sun);
const grid=new THREE.GridHelper(16,16,0x334155,0x334155);grid.position.y=-0.55;scene.add(grid);
const p={...config.parameters};const state={paused:false,highlight:true,forces:config.showForces!==false};
let world,blockBody,rampBody,blockMesh,rampMesh,forceArrows=[];
const material=(color)=>new THREE.MeshStandardMaterial({color,roughness:0.65});
const box=(dimensions,color)=>new THREE.Mesh(new THREE.BoxGeometry(...dimensions),material(color));
function tag(obj,text,y=0.8){const d=document.createElement('div');d.className='label';d.textContent=text;const label=new CSS2DObject(d);label.position.set(0,y,0);obj.add(label)}
function renderLabels(){ // regenerate labels safely each reset
  const objects={block:blockMesh,ramp:rampMesh};
  for(const obj of Object.values(objects)) for(const child of [...obj.children]) if(child.isCSS2DObject) obj.remove(child);
  for(const a of config.annotations||[]){const obj=objects[a.target];if(obj)tag(obj,a.target==='ramp'?a.text:a.text,a.target==='ramp'?0.15:0.75)}
}
function createArrow(color){const a=new THREE.ArrowHelper(new THREE.Vector3(0,1,0),new THREE.Vector3(),1,color,0.22,0.12);scene.add(a);return a}
function updateArrows(){const pos=blockMesh.position;const theta=THREE.MathUtils.degToRad(p.angleDegrees);
  const dirs=[new THREE.Vector3(0,-1,0),new THREE.Vector3(Math.sin(theta),Math.cos(theta),0),new THREE.Vector3(Math.cos(theta),-Math.sin(theta),0)];
  // The orange arrow shows the uphill friction direction only when the block is sliding downhill.
  dirs[2].multiplyScalar(-1);dirs[2].set(-Math.cos(theta),Math.sin(theta),0);
  const lengths=[Math.min(2.1,0.6+p.gravity/12),1.2,1.1];
  forceArrows.forEach((a,i)=>{a.visible=state.forces;a.position.copy(pos);a.position.z+=0.65;a.setDirection(dirs[i].normalize());a.setLength(lengths[i],0.24,0.12)});
}
function updatePhysics(){
  world=new RAPIER.World({x:0,y:-p.gravity,z:0});
  // Ramp slopes down toward +x. Rotation around z is negative.
  const rad=THREE.MathUtils.degToRad(p.angleDegrees),q=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),-rad);
  const rd=RAPIER.RigidBodyDesc.fixed().setTranslation(0,0,0).setRotation({x:q.x,y:q.y,z:q.z,w:q.w});rampBody=world.createRigidBody(rd);
  world.createCollider(RAPIER.ColliderDesc.cuboid(4,0.22,1.5).setFriction(p.friction),rampBody);
  rampMesh.position.set(0,0,0);rampMesh.quaternion.copy(q);
  const x=-2.3,y=Math.tan(rad)*2.3+0.22/Math.cos(rad)+0.38;
  const bd=RAPIER.RigidBodyDesc.dynamic().setTranslation(x,y,0).setCanSleep(false);
  blockBody=world.createRigidBody(bd);world.createCollider(RAPIER.ColliderDesc.cuboid(.45,.38,.45).setDensity(p.massKg/(.9*.76*.9)).setFriction(p.friction),blockBody);
  blockMesh.position.set(x,y,0);blockMesh.quaternion.identity();
}
blockMesh=box([.9,.76,.9],0x38bdf8);rampMesh=box([8,.44,3],0x64748b);scene.add(blockMesh,rampMesh);
forceArrows=[createArrow(0xff6b6b),createArrow(0x22c55e),createArrow(0xf59e0b)];
renderLabels();updatePhysics();
const gui=new GUI({container:document.querySelector('#gui'),title:'Parameters'});
gui.add(p,'angleDegrees',5,55,1).name('Ramp angle (°)').onFinishChange(updatePhysics);
gui.add(p,'massKg',0.5,12,0.5).name('Mass (kg)').onFinishChange(updatePhysics);
gui.add(p,'gravity',0,20,0.1).name('Gravity (m/s²)').onFinishChange(updatePhysics);
gui.add(p,'friction',0,1.5,0.05).name('Friction coefficient').onFinishChange(updatePhysics);
const pause=document.querySelector('#pause');pause.onclick=()=>{state.paused=!state.paused;pause.textContent=state.paused?'Resume':'Pause'};
document.querySelector('#reset').onclick=updatePhysics;
document.querySelector('#highlight').onclick=()=>{state.highlight=!state.highlight};
document.querySelector('#forces').onclick=()=>{state.forces=!state.forces};
katex.render(String.raw`F_{\parallel}=mg\sin\theta,\quad N=mg\cos\theta`,document.querySelector('#equation'),{throwOnError:false,displayMode:true});
const clock=new THREE.Clock();let accumulator=0;
function resize(){let w=viewport.clientWidth,h=viewport.clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h);labels.setSize(w,h)}
new ResizeObserver(resize).observe(viewport);resize();
function loop(){requestAnimationFrame(loop);const dt=Math.min(clock.getDelta(),0.05);if(!state.paused){accumulator+=dt;while(accumulator>=1/60){world.step();accumulator-=1/60}}
 const pos=blockBody.translation(),q=blockBody.rotation();blockMesh.position.set(pos.x,pos.y,pos.z);blockMesh.quaternion.set(q.x,q.y,q.z,q.w);
 blockMesh.material.emissive.setHex(state.highlight&&config.highlight==='block'?0x164e63:0x000000);
 rampMesh.material.emissive.setHex(state.highlight&&config.highlight==='ramp'?0x334155:0x000000);
 updateArrows();const v=blockBody.linvel();document.querySelector('#readout').textContent=`Speed: ${Math.hypot(v.x,v.y,v.z).toFixed(2)} m/s • Gravity (red) • Normal (green) • Friction direction (orange)`;
 controls.update();renderer.render(scene,camera);labels.render(scene,camera);
}
loop();
