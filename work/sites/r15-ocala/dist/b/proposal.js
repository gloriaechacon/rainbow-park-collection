const detail=document.querySelector('.investment-detail');
function revealInvestment(){const id=decodeURIComponent(location.hash.slice(1));const target=id&&document.getElementById(id);if(target&&detail.contains(target)){detail.open=true;requestAnimationFrame(()=>target.scrollIntoView());}}
addEventListener('hashchange',revealInvestment);revealInvestment();
detail.addEventListener('toggle',()=>{if(detail.open)dispatchEvent(new Event('resize'));});
if(matchMedia('(prefers-reduced-motion: reduce)').matches){document.getElementById('hero-video').pause();document.getElementById('video-toggle').textContent='Reproducir';}
