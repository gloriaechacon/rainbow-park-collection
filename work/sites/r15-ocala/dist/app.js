const menu=document.querySelector('.menu-toggle');
menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));document.querySelector('.topbar').classList.toggle('menu-open',open)});
document.querySelectorAll('.topbar nav a').forEach(a=>a.addEventListener('click',()=>{closeMenu()}));
const video=document.querySelector('#hero-video'),toggle=document.querySelector('#video-toggle');
const motion=matchMedia('(prefers-reduced-motion: reduce)');
function syncVideo(){toggle.textContent=video.paused?'Reproducir ▶':'Pausar II';toggle.setAttribute('aria-label',video.paused?'Reproducir video':'Pausar video')}
if(motion.matches)video.pause();video.addEventListener('play',syncVideo);video.addEventListener('pause',syncVideo);syncVideo();
let manuallyPaused=false;toggle.addEventListener('click',()=>{manuallyPaused=!video.paused;if(video.paused)video.play().catch(syncVideo);else video.pause()});new IntersectionObserver(entries=>{if(entries[0].isIntersecting&&!manuallyPaused&&!motion.matches)video.play().catch(syncVideo);else if(!entries[0].isIntersecting)video.pause()},{threshold:.15}).observe(video);
const dock=document.querySelector('.chapter-dock');
const chapters=[...document.querySelectorAll('.chapter')];
function updateChapter(){dock.classList.toggle('visible',scrollY>innerHeight*.55);const current=chapters.filter(s=>s.getClientRects().length&&s.getBoundingClientRect().top<innerHeight*.45).at(-1);document.querySelectorAll('.chapter-dock a').forEach(a=>{const active=a.dataset.section===current?.id;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current')})}
let ticking=false;addEventListener('scroll',()=>{if(!ticking){requestAnimationFrame(()=>{updateChapter();ticking=false});ticking=true}},{passive:true});updateChapter();
const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('in-view');observer.unobserve(entry.target)}}),{threshold:.08});
document.querySelectorAll('.territory-intro,.territory-layout,.collection-title,.bridge,.contact-layout').forEach(el=>{el.classList.add('reveal');observer.observe(el)});
document.querySelectorAll('.context-stories details').forEach(detail=>detail.addEventListener('toggle',()=>{if(detail.open)document.querySelectorAll('.context-stories details').forEach(other=>{if(other!==detail)other.open=false})}));
const lotDialog=document.querySelector('#lot-dialog');document.querySelector('#lot-detail').addEventListener('click',()=>{document.querySelector('#dialog-lot-number').textContent=document.querySelector('#lot-number').textContent;lotDialog.showModal()});document.querySelector('#lot-to-homes').addEventListener('click',()=>lotDialog.close());document.querySelector('#about-demo').addEventListener('click',()=>document.querySelector('#demo-dialog').showModal());document.querySelectorAll('dialog').forEach(dialog=>{dialog.querySelector('.dialog-close').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close()}})});
let interest='Lote';document.querySelectorAll('[data-interest]').forEach(button=>button.addEventListener('click',()=>{interest=button.dataset.interest;document.querySelectorAll('[data-interest]').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',String(b===button))})}));
document.querySelector('#download-brief').addEventListener('click',()=>{
 const t=s=>window.rpcI18n?.t(s)||s;
 const text=['RAINBOW PARK COLLECTION',t('Consulta para Next Fraga Real Estate'),'',t('Interés:')+' '+t(interest),t('Lote seleccionado:')+' '+document.querySelector('#lot-number').textContent,t('Modelo seleccionado:')+' '+selectedHomeName(),'',t('Mi idea:'),document.querySelector('#interest-note').value||t('Me gustaría conocer las opciones del proyecto.'),'',t('Ubicaciones según pins del cliente y contornos de Marion County. Viviendas según planos; acabados propuestos. Precio y disponibilidad a confirmar.'),t('Este resumen no ha sido enviado. Compártelo directamente con Next Fraga Real Estate.')].join('\n');
 const url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='rainbow-park-'+(window.rpcI18n?.language||'es')+'.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);document.querySelector('#brief-status').textContent='Resumen descargado. Puedes compartirlo con Next Fraga Real Estate; no se ha enviado automáticamente.';
});

// Keep modal exploration and the long page from competing for scroll and focus.
const syncModalScroll=()=>document.body.classList.toggle('modal-open',Boolean(document.querySelector('dialog[open]')));
document.querySelectorAll('dialog').forEach(dialog=>new MutationObserver(syncModalScroll).observe(dialog,{attributes:true,attributeFilter:['open']}));
function closeMenu(returnFocus=false){menu.setAttribute('aria-expanded','false');menu.querySelector('span').textContent='＋';document.querySelector('.topbar').classList.remove('menu-open');if(returnFocus)menu.focus()}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&menu.getAttribute('aria-expanded')==='true')closeMenu(true)});
document.addEventListener('click',e=>{if(!e.target.closest('.topbar')&&menu.getAttribute('aria-expanded')==='true')closeMenu()});
const selectedHomeName=()=>document.querySelector('#lotes').dataset.selectedHouse==='b'?'Casa Bell':'Casa Utah';
const syncSelection=()=>{document.querySelector('#consultation-selection').textContent=`Lote ${document.querySelector('#lot-number').textContent} · ${selectedHomeName()}`};
document.addEventListener('rpc:lot',syncSelection);document.addEventListener('rpc:home',syncSelection);syncSelection();

// The graphic modules load when exploration is nearby, or when explicitly requested.
let graphicsPromise;
function loadExploration(){if(!graphicsPromise)graphicsPromise=import('./experience3d.js?v=finishes6').then(()=>import('./space-studio.js?v=finishes6')).catch(error=>{graphicsPromise=null;document.querySelectorAll('.scene-loading').forEach(el=>el.textContent='No pudimos cargar la vista. Vuelve a intentarlo.');throw error});return graphicsPromise}
const loadObserver=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){loadExploration().catch(()=>{});loadObserver.disconnect()}},{rootMargin:'700px'});loadObserver.observe(document.querySelector('#coleccion-anterior'));loadObserver.observe(document.querySelector('#viviendas'));
let explorationReady=false;
document.addEventListener('click',async e=>{const button=e.target.closest('[data-open-placement],[data-open-tour],#compare-homes');if(!button||explorationReady)return;e.preventDefault();e.stopImmediatePropagation();button.setAttribute('aria-busy','true');try{await loadExploration();explorationReady=true;button.click()}catch{}finally{button.removeAttribute('aria-busy')}},true);
document.querySelector('#compare-homes').addEventListener('click',()=>document.querySelector('#compare-dialog').showModal());
document.querySelectorAll('[data-compare-model]').forEach(b=>b.addEventListener('click',()=>{document.querySelector(`[data-home="${b.dataset.compareModel}"]`).click();document.querySelector('#compare-dialog').close();document.querySelector(`[data-home="${b.dataset.compareModel}"]`).focus()}));
// Keep the expandable chapter menu reachable without trapping keyboard users.
menu.addEventListener('click',()=>{menu.querySelector('span').textContent=menu.getAttribute('aria-expanded')==='true'?'−':'＋'});
document.querySelector('#main-menu').addEventListener('focusout',e=>{if(e.relatedTarget&&!document.querySelector('.topbar').contains(e.relatedTarget))closeMenu()});
