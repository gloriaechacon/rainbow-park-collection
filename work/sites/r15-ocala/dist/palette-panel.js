(() => {
 const frame=document.getElementById('preview');
 const palettes={forest:{name:'Bosque · Actual',description:'Verde y marfil',colors:['#172e29','#f0eee5','#294d3f','#d3e5a3']},earth:{name:'Tierra',description:'Cálida y residencial',colors:['#3d302a','#fcf6ee','#824b35','#e4c4a6']},slate:{name:'Azul pizarra',description:'Sobria y serena',colors:['#203d50','#f1f5f5','#285a70','#c8dce3']}};
 const params=new URLSearchParams(location.search);
 let palette=Object.hasOwn(palettes,params.get('palette'))?params.get('palette'):'forest';
 const workspace=document.createElement('div');workspace.className='review-workspace';
 const stage=document.getElementById('stage');stage.before(workspace);
 const panel=document.createElement('aside');panel.className='palette-panel';panel.setAttribute('aria-label','Paletas para la portada');
 panel.innerHTML='<h2>Colores de la portada</h2><p>Prueba la misma composición con tres paletas.</p><div class="palette-options" role="group" aria-label="Paleta de color"></div><p class="palette-status" role="status" aria-live="polite"></p><p class="palette-scope">Esta ronda: encabezado y portada. Conservamos los logos y el video.</p>';
 workspace.append(panel,stage);
 const buttons=[];
 for(const [key,p] of Object.entries(palettes)){const button=document.createElement('button');button.className='palette-choice';button.dataset.palette=key;button.type='button';button.setAttribute('aria-pressed','false');button.innerHTML='<span class="palette-swatches" aria-hidden="true">'+p.colors.map(color=>'<i style="--swatch:'+color+'"></i>').join('')+'</span><strong>'+p.name+'</strong><small>'+p.description+'</small>';button.addEventListener('click',()=>{palette=key;apply();});panel.querySelector('.palette-options').append(button);buttons.push(button);}
 function apply(){
   const selected=document.querySelector('[data-version][aria-pressed="true"]').dataset.version;
   const isOriginal=selected==='original';
   buttons.forEach(b=>{b.setAttribute('aria-pressed',!isOriginal&&b.dataset.palette===palette);b.disabled=isOriginal;});
   panel.querySelector('.palette-status').textContent=isOriginal?'La versión actual conserva sus colores. Elige A o B para probar paletas.':'Seleccionada: '+palettes[palette].name;
   if(!isOriginal)frame.contentWindow.postMessage({type:'rainbow-palette',palette},location.origin);
   const href=new URL(frame.src);if(!isOriginal)href.searchParams.set('palette',palette);document.getElementById('open').href=href.href;
   const url=new URL(location.href);url.searchParams.set('version',selected);url.searchParams.set('palette',palette);history.replaceState(null,'',url);
 }
 frame.addEventListener('load',apply);
 document.querySelectorAll('[data-version]').forEach(button=>button.addEventListener('click',apply));
 if(['a','b','original'].includes(params.get('version')))document.querySelector('[data-version="'+params.get('version')+'"]').click();
 const phone=matchMedia('(max-width:650px)');
 const selectPhone=()=>{if(phone.matches)document.querySelector('[data-width="390"]').click();};
 selectPhone();phone.addEventListener('change',selectPhone);
 apply();
})();
