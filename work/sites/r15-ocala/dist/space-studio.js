import {studioURL} from './house-data.js?v=finishes6';
let selected='a';
document.addEventListener('rpc:home',e=>selected=e.detail);
document.querySelectorAll('[data-open-placement]').forEach(b=>b.onclick=()=>location.href=studioURL(selected,'lot'));
document.querySelectorAll('[data-open-tour]').forEach(b=>b.onclick=()=>location.href=studioURL(selected,'living'));
