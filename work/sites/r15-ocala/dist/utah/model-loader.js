import * as T from '../vendor/three.module.js';
export async function loadHouse(url){
 const raw=await fetch(url).then(r=>{if(!r.ok)throw Error('Modelo no disponible');return r.arrayBuffer()}),n=new DataView(raw).getUint32(12,true),g=JSON.parse(new TextDecoder().decode(new Uint8Array(raw,20,n))),start=28+n;
 const textures=await Promise.all((g.textures||[]).map(async t=>{const im=g.images[t.source],v=g.bufferViews[im.bufferView],url=URL.createObjectURL(new Blob([new Uint8Array(raw,start+(v.byteOffset||0),v.byteLength)],{type:im.mimeType}));try{const tex=await new T.TextureLoader().loadAsync(url);tex.flipY=false;tex.wrapS=tex.wrapT=T.RepeatWrapping;tex.anisotropy=8;return tex}finally{URL.revokeObjectURL(url)}}));
 const colorTex=i=>{const t=textures[i].clone();t.colorSpace=T.SRGBColorSpace;t.needsUpdate=true;return t};
 const mats=g.materials.map(m=>{const p=m.pbrMetallicRoughness,c=p.baseColorFactor||[1,1,1,1];return new T.MeshStandardMaterial({name:m.name,color:new T.Color(c[0],c[1],c[2]),roughness:p.roughnessFactor??1,metalness:p.metallicFactor??0,side:T.DoubleSide,transparent:m.alphaMode==='BLEND',opacity:c[3],depthWrite:m.alphaMode!=='BLEND',map:p.baseColorTexture?colorTex(p.baseColorTexture.index):null,normalMap:m.normalTexture?textures[m.normalTexture.index]:null,normalScale:new T.Vector2(m.normalTexture?.scale??1,m.normalTexture?.scale??1),roughnessMap:p.metallicRoughnessTexture?textures[p.metallicRoughnessTexture.index]:null,metalnessMap:p.metallicRoughnessTexture?textures[p.metallicRoughnessTexture.index]:null,envMapIntensity:.65})});
 const attr=id=>{const a=g.accessors[id],v=g.bufferViews[a.bufferView],num={VEC2:2,VEC3:3}[a.type];return new T.BufferAttribute(new Float32Array(raw,start+(v.byteOffset||0)+(a.byteOffset||0),a.count*num),num)};
 const result=new T.Group();for(const node of g.nodes){const part=new T.Group();part.name=node.name;part.userData=node.extras||{};for(const p of g.meshes[node.mesh].primitives){const geo=new T.BufferGeometry();geo.setAttribute('position',attr(p.attributes.POSITION));geo.setAttribute('normal',attr(p.attributes.NORMAL));if(p.attributes.TEXCOORD_0!==undefined)geo.setAttribute('uv',attr(p.attributes.TEXCOORD_0));const mesh=new T.Mesh(geo,mats[p.material]);mesh.castShadow=!mesh.material.transparent;mesh.receiveShadow=true;part.add(mesh)}result.add(part)}const lights=new T.Group();lights.name='Interior daylight fill';
 const isBell=url.includes('bell');const points=isBell?[[-1.5,2.15,0],[1.7,2.15,-3.6],[2.2,2.15,1.6],[-5.7,2.15,-3.6],[-5.7,2.15,2]]:[[-1,2.12,2.8],[-2.5,2.12,-.7],[6,2.12,0],[6.4,2.12,4.7],[2.5,2.12,5.4],[-5,2.12,-5.4],[-5,2.12,-2.8]];
 for(const p of points){const light=new T.PointLight(0xfff5e5,1.8,5,2);light.position.fromArray(p);light.position.y=1.65;lights.add(light)}result.add(lights);return result;
}
export function daylight(scene,renderer){
 const canvas=document.createElement('canvas');canvas.width=512;canvas.height=256;const ctx=canvas.getContext('2d'),sky=ctx.createLinearGradient(0,0,0,256);sky.addColorStop(0,'#729fbc');sky.addColorStop(.45,'#e9f1ee');sky.addColorStop(.52,'#f5edda');sky.addColorStop(1,'#7b8263');ctx.fillStyle=sky;ctx.fillRect(0,0,512,256);const glow=ctx.createRadialGradient(100,90,2,100,90,58);glow.addColorStop(0,'#ffffff');glow.addColorStop(1,'#ffffff00');ctx.fillStyle=glow;ctx.fillRect(0,0,512,256);const texture=new T.CanvasTexture(canvas);texture.colorSpace=T.SRGBColorSpace;texture.mapping=T.EquirectangularReflectionMapping;const pmrem=new T.PMREMGenerator(renderer);scene.environment=pmrem.fromEquirectangular(texture).texture;texture.dispose();pmrem.dispose();
 renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=.95;
 contactShadows(renderer);
}

// Local screen-space contact shading adds depth where furniture meets floor and
// joinery meets walls. Two passes only when the user changes a view (no idle loop).
function contactShadows(renderer){
 const target=new T.WebGLRenderTarget(1,1,{type:T.HalfFloatType,depthBuffer:true,samples:4});
 target.depthTexture=new T.DepthTexture(1,1,T.UnsignedIntType);
 const material=new T.ShaderMaterial({depthTest:false,depthWrite:false,uniforms:{
  colorBuffer:{value:target.texture},depthBuffer:{value:target.depthTexture},resolution:{value:new T.Vector2(1,1)},inverseProjection:{value:new T.Matrix4()},projection:{value:new T.Matrix4()}
 },vertexShader:`varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}`,
 fragmentShader:`
 varying vec2 vUv;uniform sampler2D colorBuffer;uniform sampler2D depthBuffer;
 uniform vec2 resolution;uniform mat4 inverseProjection;uniform mat4 projection;
 vec3 viewPosition(vec2 uv){vec4 p=inverseProjection*vec4(uv*2.-1.,texture2D(depthBuffer,uv).r*2.-1.,1.);return p.xyz/p.w;}
 void main(){vec4 color=texture2D(colorBuffer,vUv);float depth=texture2D(depthBuffer,vUv).r;
 if(depth<.99999){vec3 p=viewPosition(vUv);vec3 normal=normalize(cross(dFdx(p),dFdy(p)));float occ=0.;
 float radius=.40;vec2 pixels=vec2(projection[0][0],projection[1][1])*radius/max(.2,-p.z)*.5;
 for(int i=0;i<16;i++){float a=float(i)*2.399963;float r=sqrt((float(i)+.5)/16.);vec2 uv=vUv+vec2(cos(a),sin(a))*pixels*r;
 if(uv.x>0.&&uv.x<1.&&uv.y>0.&&uv.y<1.){vec3 d=viewPosition(uv)-p;float dist=length(d);occ+=max(0.,dot(normal,d/max(dist,.001))-.06)*(1.-smoothstep(.02,radius*1.8,dist));}}
 color.rgb*=clamp(1.-occ*.085,.48,1.);}
 gl_FragColor=color;
 #include <tonemapping_fragment>
 #include <colorspace_fragment>
 }`});
 const postScene=new T.Scene();postScene.add(new T.Mesh(new T.PlaneGeometry(2,2),material));const postCamera=new T.Camera(),render=renderer.render.bind(renderer),size=new T.Vector2();
 renderer.render=(scene,camera)=>{if(scene===postScene)return render(scene,camera);renderer.getDrawingBufferSize(size);if(target.width!==size.x||target.height!==size.y){target.setSize(size.x,size.y);material.uniforms.resolution.value.copy(size)}material.uniforms.inverseProjection.value.copy(camera.projectionMatrixInverse);material.uniforms.projection.value.copy(camera.projectionMatrix);renderer.setRenderTarget(target);render(scene,camera);renderer.setRenderTarget(null);render(postScene,postCamera)};
}
