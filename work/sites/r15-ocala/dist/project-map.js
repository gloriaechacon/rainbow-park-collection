(()=>{
 const host=document.querySelector('#investment-map');if(!host)return;
 const root=new URL('.',document.currentScript.src),side=document.querySelector('.project-map-detail'),list=document.querySelector('.project-map-list');
 const e=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const color={wec:'#a8733d',infraestructura:'#508899',empleo:'#55784d',servicios:'#9a5e75'};
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 let initialized=false;
 async function init(){if(initialized)return;initialized=true;
 try{
 const data=await fetch(new URL('inversion/project-map.json',root)).then(r=>{if(!r.ok)throw Error();return r.json()});
 const map=window.L?L.map(host,{scrollWheelZoom:false,zoomControl:false}).setView([29.190,-82.273],12):null;
 if(map)L.control.zoom({position:'bottomleft'}).addTo(map);
 const street=map&&L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}).addTo(map);
 const aerial=map&&L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Imagery © Esri, Maxar, Earthstar Geographics and GIS User Community'});
 if(!map)host.innerHTML='<p class="map-fallback">Consulta las ubicaciones y documentos en las fichas inferiores.</p>';
 const allPoints=data.locations.filter(p=>p.id!=='jockey-club'&&p.id!=='i75-sur').map(p=>[p.lat,p.lon]);allPoints.push([29.155411,-82.37]);
 const reset=()=>map?.fitBounds(allPoints,{padding:[45,45],maxZoom:12,animate:!reduced});
 const sources=Object.fromEntries(data.sources.map(s=>[s.id,s]));let filter='all',selected;
 const lines=[];
 if(map){L.marker([29.155411,-82.37],{icon:L.divIcon({className:'rainbow-map-pin',html:'<span>R</span><b>RAINBOW PARK</b>',iconSize:[36,36],iconAnchor:[18,18]}),title:'Rainbow Park — área de la colección'}).addTo(map).bindTooltip('Zona de Rainbow Park · referencia del sector');
 data.corridors.forEach(c=>c.paths.forEach(path=>{const line=L.polyline(path.map(p=>[p.lat,p.lon]),{color:'#508899',weight:5,opacity:.65}).addTo(map);line.bindTooltip('Obra FDOT · '+c.id);lines.push(line)}));}
 const markerById=new Map();const buttons=new Map();
 function select(p,fly=true){selected=p.id;
  const primary=p.projects[0];
  for(const [id,b]of buttons)b.setAttribute('aria-pressed',String(id===p.id));
  for(const [id,m]of markerById)m.getElement()?.classList.toggle('selected',id===p.id);
  side.innerHTML=`${p.image?`<figure class="map-project-image"><img src="${new URL('inversion/assets/'+p.image,root)}" alt="Render conceptual oficial del proyecto deportivo WEC"><figcaption>Propuesta · expediente público de Marion County</figcaption></figure>`:'<span class="map-detail-orbit" aria-hidden="true">↗</span>'}<div class="map-detail-body"><span class="investment-status ${e(primary.statusClass)}">${e(primary.status)}</span><h4>${e(p.name)}</h4><div class="map-detail-metric">${e(primary.metric)}<small>${e(primary.unit)}</small></div><p>${e(primary.meaning)}</p>${p.projects.length>1?`<p class="map-shared">También en este conjunto: ${p.projects.slice(1).map(x=>e(x.name)).join(' · ')}</p>`:''}<a class="map-detail-link" href="${new URL('inversion/#proyecto-'+primary.id,root)}">Explorar el proyecto y documentos ↗</a><a class="map-source" href="${e(p.sourceURL)}" target="_blank" rel="noopener">Fuente de la ubicación ↗</a><small class="map-precision">${e(p.precision)}</small></div>`;
  if(map&&fly)map.flyTo([p.lat,p.lon],p.id.startsWith('i75')?12:14,{duration:reduced?0:.8});
 }
 data.locations.forEach((p,i)=>{const b=document.createElement('button');b.innerHTML=`<span style="--pin:${color[p.category]}">${String(i+1).padStart(2,'0')}</span>${e(p.name)}`;b.setAttribute('aria-pressed','false');b.onclick=()=>select(p);buttons.set(p.id,b);list.append(b);
 if(map){const marker=L.marker([p.lat,p.lon],{title:p.name,icon:L.divIcon({className:'project-map-pin',html:`<span style="--pin:${color[p.category]}">${String(i+1).padStart(2,'0')}</span>`,iconSize:[34,34],iconAnchor:[17,17]})}).addTo(map);marker.bindTooltip(p.name,{direction:'top',offset:[0,-20]});marker.on('click',()=>select(p));markerById.set(p.id,marker)}});
 document.querySelectorAll('[data-map-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.mapFilter;document.querySelectorAll('[data-map-filter]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));const visible=data.locations.filter(p=>filter==='all'||p.category===filter);data.locations.forEach(p=>{const show=visible.includes(p);buttons.get(p.id).hidden=!show;const marker=markerById.get(p.id);if(marker){if(show)marker.addTo(map);else marker.remove()}});lines.forEach(l=>filter==='all'||filter==='infraestructura'?l.addTo(map):l.remove());if(visible.length){if(!visible.some(p=>p.id===selected))select(visible[0],false);map?.fitBounds(visible.map(p=>[p.lat,p.lon]),{padding:[60,60],maxZoom:13,animate:!reduced})}});
 document.querySelectorAll('[data-map-base]').forEach(b=>b.onclick=()=>{if(!map)return;const isAerial=b.dataset.mapBase==='aerial';map.removeLayer(isAerial?street:aerial);(isAerial?aerial:street).addTo(map);document.querySelectorAll('[data-map-base]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)))});
 document.querySelector('[data-map-reset]').onclick=reset;select(data.locations.find(p=>p.id==='wec-deportivo'),false);reset();new ResizeObserver(()=>map?.invalidateSize()).observe(host);
 }catch(err){side.innerHTML='<h4>Consulta el dossier</h4><p>Las ubicaciones no pudieron cargarse. Las fichas y sus documentos siguen disponibles.</p><a href="'+new URL('inversion/#proyectos',root)+'">Ver proyectos ↗</a>'}}
 const observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){init();observer.disconnect()}},{rootMargin:'300px'});observer.observe(host);
})();
