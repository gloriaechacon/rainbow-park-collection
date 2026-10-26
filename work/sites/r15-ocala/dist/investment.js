(() => {
  document.querySelectorAll('[data-investment-gallery]').forEach(gallery => {
    const image = gallery.querySelector('img');
    gallery.querySelectorAll('[data-gallery-src]').forEach(button => button.addEventListener('click', () => {
      image.src = button.dataset.gallerySrc;
      image.alt = button.dataset.galleryAlt;
      gallery.querySelectorAll('[data-gallery-src]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    }));
  });
  const cards = [...document.querySelectorAll('[data-project-category]')];
  document.querySelectorAll('[data-project-filter]').forEach(button => button.addEventListener('click', () => {
    const filter = button.dataset.projectFilter;
    cards.forEach(card => card.hidden = filter !== 'all' && card.dataset.projectCategory !== filter);
    document.querySelectorAll('[data-project-filter]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    const count = cards.filter(card => !card.hidden).length;
    document.querySelector('#project-count').textContent = `${count} ${count === 1 ? 'proyecto o adquisición' : 'proyectos y adquisiciones'}`;
  }));
  const search = document.querySelector('#source-search');
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  search?.addEventListener('input', () => {
    const query = normalize(search.value.trim());
    const rows = [...document.querySelectorAll('[data-source-search]')];
    rows.forEach(row => row.hidden = !normalize(row.dataset.sourceSearch+' '+row.textContent).includes(query));
    document.querySelector('#source-empty').hidden = rows.some(row => !row.hidden);
  });
  const openHash = () => {
    if (!location.hash.startsWith('#proyecto-')) return;
    const card = document.getElementById(location.hash.slice(1));
    if (!card?.matches('[data-project-category]')) return;
    if (card.hidden) document.querySelector('[data-project-filter="all"]')?.click();
    card.open = true;
  };
  openHash();
  addEventListener('hashchange', openHash);
  let printState;
  addEventListener('beforeprint', () => {
    printState = [...document.querySelectorAll('details,[data-project-category],[data-source-search]')].map(el => ({ el, open: el.open, hidden: el.hidden }));
    printState.forEach(({el}) => { el.hidden = false; if (el.tagName === 'DETAILS') el.open = true; });
  });
  addEventListener('afterprint', () => {
    printState?.forEach(({el,open,hidden}) => { el.hidden = hidden; if (el.tagName === 'DETAILS') el.open = open; });
    printState = undefined;
  });
  document.querySelector('[data-print-dossier]')?.addEventListener('click', () => window.print());
})();
