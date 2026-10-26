import * as T from '../vendor/three.module.js';
// An illustrative 23 × 44 m setting; no geometry here represents a surveyed parcel.
export function createLotEnvironment(){
 const group=new T.Group();group.name='Entorno ilustrativo · aproximadamente ¼ acre';let seed=721;
 const rnd=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296};
 const color=c=>new T.Color(c);
 function texture(kind){const c=document.createElement('canvas');c.width=c.height=512;const x=c.getContext('2d');x.fillStyle=kind==='grass'?'#78854e':kind==='bark'?'#746552':'#c8c3b4';x.fillRect(0,0,512,512);for(let i=0;i<38000;i++){let a=rnd()*512,b=rnd()*512;if(kind==='grass'){x.strokeStyle=['#8e9c5a','#607643','#b1b978','#50643b'][i%4];x.globalAlpha=.25+rnd()*.35;x.beginPath();x.moveTo(a,b);x.lineTo(a+rnd()*3-1.5,b-2-rnd()*6);x.stroke()}else if(kind==='bark'){x.fillStyle=i%2?'#473f32':'#a49776';x.globalAlpha=.2;x.fillRect(a,b,1+rnd()*2,8+rnd()*45)}else{x.fillStyle=i%2?'#eee9dd':'#8d897c';x.globalAlpha=.18;x.fillRect(a,b,1.5,1.5)}}x.globalAlpha=1;const tex=new T.CanvasTexture(c);tex.colorSpace=T.SRGBColorSpace;tex.wrapS=tex.wrapT=T.RepeatWrapping;tex.anisotropy=8;return tex}
 const lawnMap=texture('grass');lawnMap.repeat.set(11.5,22);const grass=new T.MeshStandardMaterial({map:lawnMap,roughness:1,color:'#c7cc9c'}),stoneMap=texture('stone');stoneMap.repeat.set(2,4);const stone=new T.MeshStandardMaterial({map:stoneMap,roughness:.94});const barkMap=texture('bark');barkMap.repeat.set(2,3);const bark=new T.MeshStandardMaterial({map:barkMap,roughness:1});
 function block(w,h,d,material,x,y,z){const m=new T.Mesh(new T.BoxGeometry(w,h,d),material);m.position.set(x,y,z);m.castShadow=m.receiveShadow=true;group.add(m);return m}
 const earth=new T.MeshStandardMaterial({color:'#81765e',roughness:1});block(23,.22,44,earth,0,-.32,0);block(23,.06,44,grass,0,-.18,0);
 // Shared house offset: facade (+Z) faces the short southern edge. Front porch = ~16 m.
 const drivewayParts=[block(3.6,.06,6.82,stone,-5.28,-.12,18.59),block(5,.04,1.1,stone,-1.7,-.10,16),block(1.15,.04,5.4,stone,.15,-.10,19.3)];
 const seam=new T.MeshStandardMaterial({color:'#9b978a',roughness:1});for(const z of [16.6,18.65,20.7])drivewayParts.push(block(3.6,.007,.018,seam,-5.28,-.084,z));drivewayParts.forEach(o=>o.userData.originalX=o.position.x);group.userData.setGarageSide=side=>drivewayParts.forEach(o=>o.position.x=o.userData.originalX*(side===1?-1:1));
 // Street context lies outside the parcel. No fence or amenity is represented as included.
 const road=new T.MeshStandardMaterial({color:'#555852',roughness:.96});block(90,.08,7,road,0,-.27,28.5);block(90,.09,1.6,stone,0,-.225,23.4);block(90,.12,.16,stone,0,-.24,24.28);
 const shoulderMap=texture('grass');shoulderMap.repeat.set(40,40);const shoulder=new T.Mesh(new T.PlaneGeometry(160,150),new T.MeshStandardMaterial({map:shoulderMap,color:'#adb984',roughness:1}));shoulder.rotation.x=-Math.PI/2;shoulder.position.set(0,-.45,-30);shoulder.receiveShadow=true;group.add(shoulder);
 // Thin survey-style border communicates the illustrative dimensions without a perimeter wall.
 const border=new T.Line(new T.BufferGeometry().setFromPoints([[-11.5,-.12,-22],[11.5,-.12,-22],[11.5,-.12,22],[-11.5,-.12,22],[-11.5,-.12,-22]].map(p=>new T.Vector3(...p))),new T.LineBasicMaterial({color:'#fff1c3'}));group.add(border);
 const front=new T.Line(new T.BufferGeometry().setFromPoints([new T.Vector3(-11.5,-.08,22),new T.Vector3(11.5,-.08,22)]),new T.LineBasicMaterial({color:'#efcd83'}));group.add(front);
 function label(text,x,z,width=11){const c=document.createElement('canvas');c.width=768;c.height=112;const cx=c.getContext('2d');cx.fillStyle='#203a30e8';cx.fillRect(0,0,768,112);cx.font='500 39px Arial';cx.fillStyle='#fff7df';cx.textAlign='center';cx.textBaseline='middle';cx.fillText(text,384,57);const m=new T.Mesh(new T.PlaneGeometry(width,width*112/768),new T.MeshBasicMaterial({map:new T.CanvasTexture(c),transparent:true,depthWrite:false,side:T.DoubleSide}));m.rotation.x=-Math.PI/2;m.position.set(x,-.065,z);group.add(m)}
 label('FRENTE · 76 pies aprox.',0,22.65,8);label('JARDÍN POSTERIOR',0,-9,9);
 function branch(a,b,r1,r2){const dir=new T.Vector3().subVectors(b,a),mesh=new T.Mesh(new T.CylinderGeometry(r2,r1,dir.length(),7),bark);mesh.position.copy(a).add(b).multiplyScalar(.5);mesh.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),dir.normalize());mesh.castShadow=mesh.receiveShadow=true;group.add(mesh)}
 const leafGeometry=new T.SphereGeometry(1,5,3);leafGeometry.scale(.10,.027,.23);
 const leafMat=new T.MeshStandardMaterial({color:'#ffffff',roughness:.88,side:T.DoubleSide});
 const trees=[[-8.4,-16,1.0],[7.8,-17.5,.86],[-18,-4,1.12],[19,-12,1.16],[-23,-28,1.25],[0,-36,1.24],[22,-33,1.4],[-36,-15,1.3],[38,-22,1.1],[-30,15,1.0],[31,12,1.14]];
 const leafCount=trees.length*750;const leaves=new T.InstancedMesh(leafGeometry,leafMat,leafCount);const dummy=new T.Object3D();let leafIndex=0;
 for(const [tx,tz,s]of trees){const base=new T.Vector3(tx,-.15,tz),crown=new T.Vector3(tx+.3*s,5.4*s,tz);branch(base,crown,.25*s,.10*s);
  for(let k=0;k<7;k++){const angle=k*2.399,tip=new T.Vector3(tx+Math.cos(angle)*2.3*s,(5.4+(k%3)*.6)*s,tz+Math.sin(angle)*2.5*s);branch(new T.Vector3(tx,3.1*s,tz),tip,.11*s,.025*s)}
  for(let j=0;j<750;j++){const angle=rnd()*Math.PI*2,cos=rnd()*2-1,radius=Math.cbrt(rnd()),f=Math.sqrt(1-cos*cos);dummy.position.set(tx+Math.cos(angle)*f*radius*3.1*s,(5.7+cos*radius*2)*s,tz+Math.sin(angle)*f*radius*3.15*s);dummy.rotation.set(rnd()*Math.PI,rnd()*6.28,rnd()*Math.PI);const scale=(.85+rnd()*.85)*s;dummy.scale.setScalar(scale);dummy.updateMatrix();leaves.setMatrixAt(leafIndex,dummy.matrix);leaves.setColorAt(leafIndex,color(['#425a2b','#587137','#6b8045','#7d8c51'][j%4]));leafIndex++}
 }
 leaves.castShadow=leaves.receiveShadow=true;group.add(leaves);
 // Fine blades, distributed over the open lawn. Kept clear of the house envelope and driveway.
 const bladeGeo=new T.BufferGeometry();bladeGeo.setAttribute('position',new T.Float32BufferAttribute([-.015,0,0,.015,0,0,.009,.15,0],3));bladeGeo.computeVertexNormals();const blades=new T.InstancedMesh(bladeGeo,new T.MeshStandardMaterial({color:'#698349',roughness:1,side:T.DoubleSide}),9000);let used=0;
 for(let i=0;i<14000&&used<9000;i++){const x=rnd()*22.8-11.4,z=rnd()*43.8-21.9;if(z>0&&z<17&&Math.abs(x)<9.3)continue;if(z>15&&((x> -7.2&&x< -3.4)||Math.abs(x-.15)<.65))continue;dummy.position.set(x,-.14,z);dummy.rotation.set(0,rnd()*Math.PI,0);dummy.scale.set(.5+rnd(),.35+rnd()*.55,1);dummy.updateMatrix();blades.setMatrixAt(used++,dummy.matrix)}blades.count=used;blades.receiveShadow=true;group.add(blades);
 return group;
}
