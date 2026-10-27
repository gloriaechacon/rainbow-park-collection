// Local, reviewed language catalog. No translation service or visitor data transfer.
const catalog=await fetch(new URL('./locales/catalog.json?v=sections2',import.meta.url)).then(r=>r.json());
const normalize=s=>s.replace(/\s+/g,' ').trim();
const byKey=new Map(Object.entries(catalog).map(([k,v])=>[normalize(k).toLowerCase(),v]));
const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const phrases=Object.keys(catalog).filter(s=>s.length>2&&catalog[s].some(t=>t!==s)).sort((a,b)=>b.length-a.length);
const fragments=new RegExp('(?<![\\p{L}\\p{N}])(?:'+phrases.map(escape).join('|')+')(?![\\p{L}\\p{N}])','giu');
let lang='es';try{lang=new URLSearchParams(location.search).get('lang')||localStorage.getItem('rpc-language')||'es'}catch{}
if(!['es','en','pt'].includes(lang))lang='es';
const original=new WeakMap(),attributes=new WeakMap();let observer;
function translated(source){
 if(lang==='es')return source;
 const idx=lang==='en'?0:1,sourceKey=normalize(source),hit=byKey.get(sourceKey.toLowerCase());
 const pick=(s,v)=>/[a-záéíóúñãõç]/i.test(s)&&s===s.toUpperCase()?v.toUpperCase():v;
 if(hit)return source.replace(source.trim(),pick(sourceKey,hit[idx]));
 return source.replace(fragments,s=>pick(s,byKey.get(normalize(s).toLowerCase())[idx]));
}
function blocked(el){return !el||Boolean(el.closest('script,style,textarea,input,option,[data-no-translate],.rpc-language-control,canvas,svg defs'))}
function textNode(node){
 if(blocked(node.parentElement)||!node.textContent.trim())return;
 let state=original.get(node);if(!state||node.data!==state.rendered)state={source:node.data,rendered:node.data};
 const output=translated(state.source);if(node.data!==output)node.data=output;state.rendered=output;original.set(node,state);
}
function attrs(el){
 if(el.closest('script,style,[data-no-translate],.rpc-language-control'))return;let states=attributes.get(el)||{};
 for(const key of ['aria-label','title','alt','placeholder']){
  if(!el.hasAttribute(key))continue;const current=el.getAttribute(key);let state=states[key];
  if(!state||current!==state.rendered)state={source:current,rendered:current};
  const output=translated(state.source);if(output!==current)el.setAttribute(key,output);state.rendered=output;states[key]=state;
 }attributes.set(el,states);
}
function walk(root){
 if(root.nodeType===3){textNode(root);return}if(root.nodeType!==1||blocked(root))return;
 attrs(root);const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT);
 while(walker.nextNode()){if(walker.currentNode.nodeType===3)textNode(walker.currentNode);else attrs(walker.currentNode)}
}
function observe(){observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['aria-label','title','alt','placeholder']})}
observer=new MutationObserver(records=>{
 observer.disconnect();const roots=new Set();
 for(const record of records){if(record.type==='characterData')textNode(record.target);else if(record.type==='attributes')attrs(record.target);else for(const n of record.addedNodes)roots.add(n)}
 roots.forEach(walk);observe();
});
const controls=[];const names={es:'Español',pt:'Português',en:'English'};
function control(host,before=null){
 if(!host)return;const label=document.createElement('label');label.className='rpc-language-control';label.dataset.noTranslate='';label.innerHTML='<span aria-hidden="true">◎</span><select aria-label="Idioma / Language / Idioma"><option value="es">Español</option><option value="pt">Português</option><option value="en">English</option></select>';
 const select=label.querySelector('select');select.value=lang;select.addEventListener('change',()=>setLanguage(select.value));controls.push(select);host.insertBefore(label,before);
}
control(document.querySelector('.topbar'),document.querySelector('.menu-toggle'));
if(!document.querySelector('.unified-header'))control(document.querySelector('.chapter-dock'));
if(!document.querySelector('.topbar')){const header=document.querySelector('body>header');control(header,header?.lastElementChild)}
function setLanguage(next){
 lang=next;try{localStorage.setItem('rpc-language',lang)}catch{}
 const u=new URL(location.href);u.searchParams.set('lang',lang);history.replaceState(history.state,'',u);
 document.documentElement.lang=lang==='pt'?'pt-BR':lang;
 observer.disconnect();walk(document.body);walk(document.querySelector('title'));controls.forEach(c=>c.value=lang);observe();
 const meta=document.querySelector('meta[name="description"]');if(meta){meta.dataset.originalDescription??=meta.content;meta.content=translated(meta.dataset.originalDescription)}
 document.dispatchEvent(new CustomEvent('rpc:language',{detail:{language:lang,name:names[lang]}}));
}
// Preserve the chosen language in links and shared viewer URLs, while leaving original PDFs intact.
document.addEventListener('click',event=>{
 const a=event.target.closest('a[href]');if(!a||a.hasAttribute('download'))return;
 const url=new URL(a.href,location.href);if(url.origin!==location.origin||!(/\/$|\.html$/.test(url.pathname)))return;
 url.searchParams.set('lang',lang);a.href=url.href;
},true);
window.rpcI18n={t:translated,get language(){return lang},setLanguage};
setLanguage(lang);
