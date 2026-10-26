import * as THREE from './vendor/three.module.js';
import {houses,lotExample,lotOffset} from './house-data.js?v=finishes6';
import {loadHouse,daylight} from './utah/model-loader.js?v=finishes6';

const colors = {forest:0x426b4b, selected:0xd5e68f, grass:0x91ad80, cream:0xeee9dc, road:0xb9b6a8};
const mat = (color, extra={}) => new THREE.MeshStandardMaterial({color,roughness:0.92,...extra});
const box = (w,h,d,color) => new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat(color));
const addBox = (group,w,h,d,color,x,y,z) => { const o=box(w,h,d,color); o.position.set(x,y,z); group.add(o); return o; };
function makeRenderer(container, scene, camera, draw) {
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.75));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.05;
  container.querySelector('.scene-loading')?.remove();
  container.append(renderer.domElement);
  const resize=()=>{const w=container.clientWidth,h=container.clientHeight;if(!w||!h)return;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();draw();};
  new ResizeObserver(resize).observe(container);
  resize();
  return renderer;
}
function addLights(scene){scene.add(new THREE.HemisphereLight(0xe9f2e7,0x738268,2.1));const sun=new THREE.DirectionalLight(0xffe8bd,2.3);sun.position.set(-16,28,12);scene.add(sun);}
function labelTexture(text){const c=document.createElement('canvas');c.width=160;c.height=80;const g=c.getContext('2d');g.fillStyle='#173927';g.fillRect(0,0,160,80);g.fillStyle='#ffffff';g.font='bold 43px Manrope, sans-serif';g.textAlign='center';g.textBaseline='middle';g.fillText(text,80,43);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;}
function addTree(group,x,z,size=1){addBox(group,.13*size,.8*size,.13*size,0x715f45,x,.4*size,z);const crown=new THREE.Mesh(new THREE.IcosahedronGeometry(.7*size,1),mat(0x3e7049));crown.position.set(x,1.07*size,z);group.add(crown);}
function addNeighbor(group,x,z,variant=0){addBox(group,2.5,1.5,2,variant%2?0xd9cdbb:0xe4dfd2,x,.8,z);const roof=new THREE.Mesh(new THREE.ConeGeometry(1.85,.85,4),mat(variant%2?0x5a574a:0x77715d));roof.rotation.y=Math.PI/4;roof.position.set(x,1.95,z);group.add(roof);addBox(group,.75,.65,.03,0x48646a,x-.35,.9,z+1.02);}
function genericScene(container){

  const scene=new THREE.Scene();scene.background=new THREE.Color(0xc9d5c4);scene.fog=new THREE.Fog(0xc9d5c4,68,118);addLights(scene);
  const camera=new THREE.PerspectiveCamera(46,1,.1,150);
  let azimuth=.39,elevation=29,distance=43,top=false,renderer;
  const draw=()=>{camera.zoom=Math.min(1,camera.aspect/1.25);camera.updateProjectionMatrix();camera.position.set(Math.sin(azimuth)*distance,elevation,Math.cos(azimuth)*distance);camera.lookAt(0,0,0);renderer?.render(scene,camera);};
  const earth=box(62,.28,44,0x94ae83);earth.position.y=-.2;scene.add(earth);
  const roadGroup=new THREE.Group();scene.add(roadGroup);
  const road1=addBox(roadGroup,64,.045,3.2,colors.road,0,.01,0);road1.rotation.y=-.14;
  addBox(roadGroup,2.7,.05,46,colors.road,-11,.02,0);
  addBox(roadGroup,2.5,.05,46,colors.road,12,.02,0);
  const accents=new THREE.Group();scene.add(accents);
  for(let i=0;i<34;i++){const x=-29+(i*17%58),z=-19+(i*23%39);if(Math.abs(z)<2.8||Math.abs(x+11)<2.5||Math.abs(x-12)<2.5)continue;addTree(accents,x,z,.6+(i%4)*.15);}
  [[-26,-15],[-12,-16],[-3,-16],[10,-16],[24,-15],[-27,16],[-12,17],[-2,17],[11,17],[25,16],[-29,-3],[29,-4]].forEach(([x,z],i)=>addNeighbor(accents,x,z,i));
  const positions=[[-22,-11],[-17,-11],[-5,-11],[2,-11],[19,-11],[-23,-5],[-17,-5],[-4,-5],[5,-5],[21,-5],[-23,10],[-17,10],[-4,10],[4,10],[21,10]];
  const lotMeshes=[];const labels=[];
  positions.forEach(([x,z],index)=>{
    const mesh=addBox(scene,3.45,.14,3.2,colors.forest,x,.12,z);mesh.userData.lot=index+1;lotMeshes.push(mesh);
    const outline=new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry),new THREE.LineBasicMaterial({color:0xd7e6c7}));outline.position.copy(mesh.position);scene.add(outline);
    const label=new THREE.Mesh(new THREE.PlaneGeometry(1.15,.57),new THREE.MeshBasicMaterial({map:labelTexture(String(index+1).padStart(2,'0')),transparent:false}));label.rotation.x=-Math.PI/2;label.position.set(x,.205,z);scene.add(label);labels.push(label);
  });
  const picker=document.querySelector('#lot-picker');
  const pickButtons=[];
  const selectLot=(number)=>{
    document.querySelectorAll("[data-plan-lot]").forEach(b=>b.setAttribute("aria-pressed",String(Number(b.dataset.planLot)===number)));
    lotMeshes.forEach((mesh,i)=>mesh.material.color.setHex(i+1===number?colors.selected:colors.forest));
    pickButtons.forEach((button,i)=>{button.classList.toggle('active',i+1===number);button.setAttribute('aria-pressed',String(i+1===number));});
    document.querySelector('#lot-number').textContent=String(number).padStart(2,'0');document.dispatchEvent(new CustomEvent('rpc:lot',{detail:number}));
    draw();
  };
  positions.forEach((_,i)=>{const b=document.createElement('button');b.type='button';b.textContent=String(i+1).padStart(2,'0');b.setAttribute('aria-label',`Seleccionar lote de ejemplo ${i+1}`);b.addEventListener('click',()=>selectLot(i+1));picker.append(b);pickButtons.push(b);});
  selectLot(Number(document.querySelector('#lotes')?.dataset.selectedLot)||1);
  const plan=document.querySelector('#lot-plan');
  plan.innerHTML=`<div class="lot-plan-sheet"><svg viewBox="0 0 720 460" preserveAspectRatio="none" aria-hidden="true"><defs><pattern id="parcel-grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#6f8960" stroke-width=".5" opacity=".2"/></pattern><pattern id="groves" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="9" cy="9" r="2" fill="#789265" opacity=".3"/></pattern></defs><rect width="720" height="460" fill="#d9e1cb"/><rect width="720" height="460" fill="url(#parcel-grid)"/><path d="M0 0H250L180 130 0 190ZM540 0H720V160L590 110ZM0 320L130 365 270 460H0ZM540 360L720 300V460H600Z" fill="url(#groves)"/><path d="M0 241L720 195M227 0V460M481 0V460" fill="none" stroke="#b3bea4" stroke-width="29"/><path d="M0 241L720 195M227 0V460M481 0V460" fill="none" stroke="#f5f2e5" stroke-width="23"/><g fill="#bac5ac" stroke="#f3f1e6" stroke-width="3"><path d="M100 25h45v28h-45zM285 25h43v28h-43zM410 30h45v28h-45zM555 26h45v28h-45zM94 400h45v28h-45zM290 400h45v28h-45zM420 400h45v28h-45zM560 400h45v28h-45z"/></g></svg>${positions.map(([x,z],i)=>`<button data-plan-lot="${i+1}" style="left:${[13,26,44,57,80][i%5]}%;top:${[26,45,76][Math.floor(i/5)]}%" aria-pressed="${i===0}" aria-label="Seleccionar lote de ejemplo ${i+1} desde el plano">${String(i+1).padStart(2,'0')}</button>`).join('')}<span class="plan-key"><i></i> Lotes de ejemplo <i></i> Selección</span></div>`;
  plan.querySelectorAll('[data-plan-lot]').forEach(b=>b.addEventListener('click',()=>selectLot(Number(b.dataset.planLot))));
  function activate3D(){if(renderer)return;
  try{renderer=makeRenderer(container,scene,camera,draw);}catch(e){container.innerHTML='<div class="scene-unavailable">La vista 3D no está disponible en este dispositivo. Puedes seleccionar cada ficha con los números inferiores.</div>';return;}
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();let drag=null;
  const canvas=renderer.domElement;
  canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,azimuth,elevation,moved:false};canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>5)drag.moved=true;if(drag.moved){azimuth=drag.azimuth-dx*.006;elevation=THREE.MathUtils.clamp(drag.elevation+dy*.11,17,58);top=false;draw();}});
  canvas.addEventListener('pointerup',e=>{if(drag&&!drag.moved){const r=canvas.getBoundingClientRect();pointer.set((e.clientX-r.left)/r.width*2-1,-((e.clientY-r.top)/r.height*2-1));raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(lotMeshes)[0];if(hit)selectLot(hit.object.userData.lot);}drag=null;});canvas.addEventListener('pointercancel',()=>drag=null);
    draw();
  }
  document.querySelectorAll('[data-lot-view]').forEach(b=>b.addEventListener('click',()=>{const is3D=b.dataset.lotView==='3d';plan.hidden=is3D;container.hidden=!is3D;document.querySelector('.map-controls').hidden=!is3D;document.querySelectorAll('[data-lot-view]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.querySelector('#atlas-hint').textContent=is3D?'Arrastra a los lados para girar · Usa + / − para el zoom':'Selecciona un número para explorar su ficha · Esquema sin escala';if(is3D)activate3D();draw()}));
  document.querySelector('#map-zoom-in').addEventListener('click',()=>{distance=Math.max(27,distance-6);draw()});document.querySelector('#map-zoom-out').addEventListener('click',()=>{distance=Math.min(75,distance+6);draw()});container.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();if(e.key==='ArrowLeft')azimuth-=.15;if(e.key==='ArrowRight')azimuth+=.15;if(e.key==='ArrowUp')elevation=Math.min(58,elevation+3);if(e.key==='ArrowDown')elevation=Math.max(17,elevation-3);draw()});
  document.querySelector('#map-angle').addEventListener('click',e=>{top=!top;e.currentTarget.textContent=top?'Perspectiva':'Vista superior';if(top){azimuth=0;elevation=59;distance=35;}else{azimuth=.39;elevation=29;distance=43;}draw();});
  document.querySelector('#map-reset').addEventListener('click',()=>{azimuth=.39;elevation=29;distance=43;top=false;document.querySelector('#map-angle').textContent='Vista superior';draw();});
  draw();
}

function homeScene(container){
 const scene=new THREE.Scene();scene.background=new THREE.Color('#e8e8e1');scene.add(new THREE.HemisphereLight(0xf5f6ff,0xaaa294,1.15));
 const ground=new THREE.Mesh(new THREE.CircleGeometry(25,80),mat(0xc4cbb7));ground.rotation.x=-Math.PI/2;ground.position.y=-.18;ground.receiveShadow=true;scene.add(ground);
 const sun=new THREE.DirectionalLight(0xfff1d6,2.4);sun.position.set(-14,25,20);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-24,right:24,top:24,bottom:-24,near:1,far:110});sun.shadow.normalBias=.008;sun.shadow.bias=-.00006;scene.add(sun);
 const camera=new THREE.PerspectiveCamera(40,1,.1,250);let azimuth=.20,elevation=6,distance=26,renderer,home='a',view='model',environmentOn=false,environmentGroup,environmentPromise;
 const target=new THREE.Vector3(0,1.6,0),models={},promises={};
 const plan=document.querySelector('#home-plan'),poster=document.querySelector('#home-poster'),hint=document.querySelector('.home-instruction');
 const draw=()=>{camera.position.set(Math.sin(azimuth)*distance,elevation,Math.cos(azimuth)*distance);camera.lookAt(target);camera.zoom=Math.min(1,camera.aspect/1.2);camera.updateProjectionMatrix();renderer?.render(scene,camera)};
 function syncModels(){Object.entries(models).forEach(([key,model])=>{model.visible=key===home;model.position.z=environmentOn?lotOffset(houses[key]):0;model.children.filter(n=>n.userData.roof).forEach(n=>n.visible=view!=='cutaway')});if(environmentGroup){environmentGroup.visible=environmentOn;environmentGroup.scale.set(lotExample.width/23,1,lotExample.depth/44);environmentGroup.userData.setGarageSide?.(houses[home].garageSide)}}
 function ensureModel(){if(!renderer){try{renderer=makeRenderer(container,scene,camera,draw);daylight(scene,renderer);let drag;renderer.domElement.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,azimuth,elevation};renderer.domElement.setPointerCapture(e.pointerId)});renderer.domElement.addEventListener('pointermove',e=>{if(!drag)return;azimuth=drag.azimuth-(e.clientX-drag.x)*.007;elevation=THREE.MathUtils.clamp(drag.elevation+(e.clientY-drag.y)*.06,3,environmentOn?75:40);draw()});for(const ev of ['pointerup','pointercancel'])renderer.domElement.addEventListener(ev,()=>drag=null)}catch{hint.textContent='Vista 3D no disponible. Puedes consultar el plano arquitectónico.';return}}
 if(!promises[home]){const key=home;hint.textContent='CARGANDO '+houses[key].name.toUpperCase()+'…';promises[key]=loadHouse(houses[key].model).then(model=>{models[key]=model;scene.add(model);syncModels();if(home===key)hint.textContent='MODELO SEGÚN PLANOS · ACABADOS PROPUESTOS · ARRASTRA PARA GIRAR';draw()}).catch(()=>{delete promises[key];hint.textContent='No se pudo cargar el modelo. Consulta su plano o vuelve a intentarlo.'})}syncModels();draw()}
 function showView(next){view=next;const is3d=view==='model'||view==='cutaway';plan.hidden=view!=='plan';poster.hidden=view!=='image';container.hidden=!is3d;document.querySelector('.home-environment-controls').hidden=!is3d;document.querySelector('#home-environment-info').hidden=!environmentOn||!is3d;document.querySelectorAll('[data-home-view]').forEach(b=>{b.classList.toggle('active',b.dataset.homeView===view);b.setAttribute('aria-pressed',String(b.dataset.homeView===view));if(b.dataset.homeView==='image')b.hidden=home!=='a'});for(const id of ['home-zoom-in','home-zoom-out','home-reset'])document.getElementById(id).hidden=!is3d;
 hint.textContent=view==='plan'?'PLANO ARQUITECTÓNICO DEL CLIENTE · ABRE EL PDF PARA VER LAS COTAS':view==='image'?'CONCEPTO DE ACABADOS · IMAGEN GENERADA':'MODELO SEGÚN PLANOS · ACABADOS PROPUESTOS';if(view==='cutaway'){elevation=28;distance=14;azimuth=.08;target.set(0,0,environmentOn?lotOffset(houses[home]):0)}if(is3d)ensureModel();syncModels();draw()}
 function selectHome(key){home=key;document.querySelector('#lotes').dataset.selectedHouse=key;setEnvironment(false);const d=houses[key];for(const [id,value]of Object.entries({'home-kicker':key==='a'?'01 / UTAH + ANEXO':'02 / BELL','home-title':d.name,'home-copy':d.description,'home-floors':'1 planta','home-rooms':d.rooms,'home-size':d.living.toLocaleString('en-US')+' ft²'}))document.getElementById(id).textContent=value;document.querySelector('#home-area-label').textContent='ÁREA HABITABLE · SEGÚN PLANO';document.querySelectorAll('[data-home]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.home===key)));plan.innerHTML=`<a href="${d.pdf}" target="_blank" rel="noopener" aria-label="Abrir plano arquitectónico de ${d.name}"><img src="${d.plan}" alt="Plano arquitectónico original de ${d.name}"><span>Abrir plano original y cotas ↗</span></a>`;document.querySelector('#home-source-plan').href=d.pdf;document.querySelector('#home-source-plan').textContent='Plano arquitectónico de '+d.name+' ↗';showView('model');document.dispatchEvent(new CustomEvent('rpc:home',{detail:key}));}
 document.querySelectorAll('[data-home]').forEach(b=>b.onclick=()=>selectHome(b.dataset.home));document.querySelectorAll('[data-home-view]').forEach(b=>b.onclick=()=>showView(b.dataset.homeView));
 document.querySelector('#home-zoom-in').onclick=()=>{distance=Math.max(12,distance-3);draw()};document.querySelector('#home-zoom-out').onclick=()=>{distance=Math.min(environmentOn?110:65,distance+4);draw()};document.querySelector('#home-reset').onclick=()=>{if(environmentOn){environmentCamera('aerial');return}azimuth=.20;elevation=6;distance=26;target.set(0,1.6,0);showView('model')};
 container.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();if(e.key==='ArrowLeft')azimuth-=.15;if(e.key==='ArrowRight')azimuth+=.15;if(e.key==='ArrowUp')elevation=Math.min(75,elevation+2);if(e.key==='ArrowDown')elevation=Math.max(3,elevation-2);draw()});
 function environmentCamera(which){const poses={aerial:[.3,43,54,0],front:[.05,9,42,9],garden:[Math.PI+.3,14,40,-1]};const [az,el,dist,z]=poses[which];azimuth=az;elevation=el;distance=dist;target.set(0,1.6,z);document.querySelectorAll('[data-environment-camera]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.environmentCamera===which)));draw()}
 function setEnvironment(enabled){environmentOn=enabled;ground.visible=!enabled;scene.background.set(enabled?'#b9d0d5':'#e8e8e1');scene.fog=enabled?new THREE.Fog('#b9d0d5',70,155):null;const toggle=document.querySelector('#home-environment');toggle.setAttribute('aria-pressed',String(enabled));toggle.textContent=enabled?'− Quitar entorno':'＋ Entorno · 0.24 acres';document.querySelector('#home-environment-info').hidden=!enabled;syncModels();if(!enabled){target.set(0,1.6,0);azimuth=.2;elevation=6;distance=26;draw();return}showView('model');environmentCamera('aerial');if(!environmentPromise){toggle.setAttribute('aria-busy','true');environmentPromise=import('./utah/lot-environment.js?v=collection14').then(({createLotEnvironment})=>{environmentGroup=createLotEnvironment();scene.add(environmentGroup);syncModels();draw()}).catch(()=>{environmentPromise=null;setEnvironment(false);hint.textContent='El entorno no pudo cargarse. Puedes volver a intentarlo.'}).finally(()=>toggle.removeAttribute('aria-busy'))}draw()}
 document.querySelector('#home-environment').onclick=()=>setEnvironment(!environmentOn);document.querySelectorAll('[data-environment-camera]').forEach(b=>b.onclick=()=>environmentCamera(b.dataset.environmentCamera));document.addEventListener('rpc:home',e=>{if(['a','b'].includes(e.detail)&&e.detail!==home)selectHome(e.detail)});selectHome(document.querySelector('#lotes').dataset.selectedHouse||'a');
}
genericScene(document.querySelector('#lot-scene'));
let homeReady=false;
function initHome(){if(homeReady)return;homeReady=true;homeScene(document.querySelector('#home-scene'))}
const homeObserver=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){initHome();homeObserver.disconnect()}},{rootMargin:'400px'});homeObserver.observe(document.querySelector('#viviendas'));
document.querySelectorAll('[data-home],[data-open-placement],[data-open-tour],#compare-homes').forEach(b=>b.addEventListener('click',initHome,{capture:true}));
