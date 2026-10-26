from pathlib import Path
import json
D=Path('work/sites/r15-ocala/dist');R=Path('work/research-ocala')
d=json.loads((R/'investment-data.json').read_text());loc=json.loads((R/'project-locations.json').read_text())
lookup={p['id']:p for p in d['projects']}
for p in loc['locations']:
 p['projects']=[lookup[x] for x in p['projectIds']];p['category']=p['projects'][0]['category']
 if p['id']=='wec-deportivo':p['projects'].append(lookup['sports-campos']);p['image']='wec-propuesta-diurna.jpg'
loc['sources']=d['sources'];loc['corridors']=json.loads((R/'fdot-corridors.json').read_text());(D/'inversion/project-map.json').write_text(json.dumps(loc,ensure_ascii=False))
block='''<section class="project-atlas" id="mapa-inversiones" aria-labelledby="project-map-heading"><div class="atlas-heading"><div><span class="eyebrow">OCALA / GEOGRAFÍA DEL CRECIMIENTO</span><h3 id="project-map-heading">Una nueva mirada<br><em>al entorno de tu inversión.</em></h3></div><p>Acércate a cada proyecto. Descubre qué se está desarrollando, dónde se encuentra y qué aporta a la región.</p></div><div class="project-map-filters" role="group" aria-label="Categorías del mapa"><button data-map-filter="all" aria-pressed="true">Todos</button><button data-map-filter="wec" aria-pressed="false">WEC y adquisiciones</button><button data-map-filter="infraestructura" aria-pressed="false">Conectividad</button><button data-map-filter="empleo" aria-pressed="false">Industria</button><button data-map-filter="servicios" aria-pressed="false">Salud</button></div><div class="project-map-shell"><div class="project-map-view"><div id="investment-map" aria-label="Mapa de los proyectos de Ocala"></div><div class="project-map-tools"><button data-map-base="street" aria-pressed="true">Mapa</button><button data-map-base="aerial" aria-pressed="false">Satélite</button><button data-map-reset>Ver entorno ↗</button></div><div class="project-map-caption">RAINBOW PARK · OCALA · MARION COUNTY</div></div><aside class="project-map-detail" aria-live="polite"><span class="eyebrow">EXPLORA EL TERRITORIO</span><h4>Los proyectos,<br>en su lugar.</h4><p>Cargando ubicaciones y documentos…</p></aside></div><div class="project-map-list" aria-label="Seleccionar un proyecto del mapa"></div><p class="project-map-note">Marcadores de referencia de direcciones, accesos o sectores. Las líneas de I-75 proceden de los mapas de FDOT. Selecciona una ficha para consultar su ubicación y fuente.</p></section>'''
for file,prefix in [(D/'index.html',''),(D/'inversion/index.html','../')]:
 s=file.read_text()
 if 'id="mapa-inversiones"' not in s:
  anchor='<div class="investment-feature">' if not prefix else '<section id="proyectos"'
  pos=s.index(anchor);s=s[:pos]+block+s[pos:]
 if 'project-map.css' not in s:s=s.replace('</head>',f'<link rel="stylesheet" href="{prefix}vendor/leaflet/leaflet.css"><link rel="stylesheet" href="{prefix}project-map.css?v=2"></head>')
 if 'project-map.js' not in s:s=s.replace('</body>',f'<script src="{prefix}vendor/leaflet/leaflet.js" defer></script><script src="{prefix}project-map.js?v=2" defer></script></body>')
 file.write_text(s)
