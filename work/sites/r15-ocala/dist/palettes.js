(() => {
 const choices=['forest','earth','slate'];
 const apply=value=>{if(choices.includes(value))document.body.dataset.palette=value;};
 apply(new URLSearchParams(location.search).get('palette')||'forest');
 addEventListener('message',event=>{if(event.origin!==location.origin||event.source!==parent||event.data?.type!=='rainbow-palette')return;apply(event.data.palette);});
})();
