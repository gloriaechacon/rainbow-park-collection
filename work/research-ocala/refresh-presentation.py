from pathlib import Path
import json,re
p=Path('work/research-ocala/investment-data.json');d=json.loads(p.read_text())
notes={
'classic-mile':'Adquisición reportada por prensa a partir de registros públicos. El antecedente urbanístico de 2024 corresponde a la etapa de Martelli y sitúa el predio en el Farmland Preservation Area. El programa futuro del comprador se incorporará cuando esté publicado.',
'sports-campos':'Primera fase anunciada por WEC. Su programa se presenta por separado del expediente urbanístico general para identificar las fases de expansión.',
'shoppes':'Calendario de apertura publicado por el promotor; la ficha se actualizará con la inauguración y los comercios confirmados.',
'manor':'Instalación operativa del campus WEC, con oferta propia de gastronomía, reuniones y eventos.',
'eone':'Finalización y empleos previstos según la empresa. El incentivo municipal corresponde a esta misma expansión.',
'i75-norte':'Tramo SR 200–SR 326. Calendario y presupuesto de FDOT para infraestructura regional, con obras y ajustes de circulación durante la ejecución.',
'i75-sur':'Tramo regional de 23 millas que incluye Marion y Sumter. Presupuesto y calendario publicados por FDOT.',
'nw49':'El presupuesto corresponde al intercambiador. La ficha de FDOT también sitúa el futuro Buc-ee’s en el entorno del nuevo acceso.',
'heathbrook':'Centro inaugurado en enero de 2026. La fuente describe su capacidad y servicios; el importe total de inversión no está publicado en este anuncio.',
'medical-office':'Edificio de especialidades inaugurado en el área urbana de Ocala en junio de 2025.',
'jockey-club':'Adquisición de 2021 en el norte de Marion County. Se incluye como antecedente de la presencia territorial del grupo.',
'smokey-willow':'Adquisición reportada en diciembre de 2025. La cifra corresponde al precio de compra; el programa futuro se añadirá cuando se publique.'}
for x in d['projects']:
 if x['id'] in notes:x['caveat']=notes[x['id']]
 if x['id']=='classic-mile':
  x['name']='Classic Mile: escala en el corredor ecuestre'
  x['meaning']='La compra amplía la presencia de Golden Ocala Equestrian Land sobre Highway 40, en el corredor ecuestre que rodea Rainbow Park.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
p=Path('work/research-ocala/build-investment.py');s=p.read_text()
s=s.replace('<h4>Lo documentado</h4>','<h4>El proyecto</h4>').replace('<h4>Lectura para el entorno</h4>','<h4>Qué aporta a Ocala</h4>').replace('<small>Análisis de contexto; no es una proyección de rentabilidad.</small>','').replace('<h4>Alcance y pendientes</h4>','<h4>Estado y alcance</h4>')
s=s.replace('El crecimiento tiene<br><em>distintos ritmos.</em>','Una región con<br><em>trayectoria de crecimiento.</em>')
s=s.replace('La vivienda de Ocala acumula crecimiento a cinco años, con una variación negativa en el último trimestre observado. Evaluar ambos horizontes permite tomar una decisión mejor informada.','El índice de vivienda de Ocala registra una apreciación acumulada del 48.14% en cinco años. Una referencia histórica para poner en perspectiva la evolución de la región, junto con los datos más recientes.')
s=s.replace('Índice de precios de <b>vivienda</b>; no mide lotes vacantes, ganancias netas ni rendimientos futuros de Rainbow Park Collection.','Índice histórico de precios de vivienda de la región. Los lotes se evalúan individualmente según ubicación, precio y costos de desarrollo.')
s=s.replace('Los planos públicos permiten entender su alcance. El desarrollo se plantea por fases y tiene condiciones de transporte e impugnaciones documentadas.','El masterplan reúne deporte, espacios interiores y servicios para ampliar la actividad del destino. Explora las imágenes oficiales y los hitos del expediente.')
s=s.replace('Qué está aprobado y qué sigue pendiente ↗','Explorar el proyecto y su documentación ↗')
s=s.replace('El desarrollo regional puede favorecer la demanda, pero no garantiza valorización ni rentabilidad. Los proyectos son de terceros y no son amenidades de Rainbow Park Collection. Cada lote requiere comprobar título, uso, acceso, servicios, costos y comparables. La colección no está afiliada al WEC.','Proyectos de terceros, presentados como contexto regional. Fechas y alcances según las fuentes enlazadas. La evaluación de cada lote considera su ubicación, precio, costos y condiciones del mercado. Rainbow Park Collection es independiente del WEC.')
s=s.replace('Más población y capacidad empresarial pueden ampliar la base de demanda. Su efecto depende de salarios, oferta nueva y capacidad de compra.','El crecimiento de población y la ampliación de empresas suman residentes, empleos y necesidades de vivienda a la región.')
s=s.replace('Las carreteras y la atención médica forman parte del entorno que valora un residente. Su beneficio se evalúa desde la ubicación exacta de cada lote.','La inversión en carreteras y atención médica refuerza la conectividad y los servicios que buscan quienes eligen establecerse en Ocala.')
s=s.replace('Deporte, hoteles, comercio y eventos pueden generar visitas y servicios. Esa actividad no se traduce automáticamente en ocupación de una vivienda.','Deporte, hoteles, comercio y eventos amplían las razones para visitar Ocala y desarrollar servicios vinculados a su actividad durante el año.')
s=s.replace('<p class="investment-disclosure">Estas relaciones son análisis de contexto, no un estudio causal ni una previsión de retorno. No se suman compras de terrenos, contratos públicos y carteras potenciales en una cifra única de inversión.</p>','')
s=s.replace('Qué está pasando.<br><em>Qué falta por pasar.</em>','El capital se mueve.<br><em>El territorio evoluciona.</em>')
s=re.sub(r'<div class="investment-faq">.*?</div><div class="decision-cta">','<div class="decision-cta">',s,flags=re.S)
s=s.replace('Las fechas y los proyectos pueden cambiar. No constituye una tasación ni una promesa de rendimiento. Las distancias dependen de la parcela; no se afirman tiempos de viaje desde lotes aún sin identificar.','Fechas sujetas a actualización. Las estadísticas describen el mercado regional y los resultados históricos no garantizan rendimientos futuros.')
# Replace the existing block; support repeatable regeneration.
s=s.replace("start=s.index('<div id=\"actualidad\"');end=s.index('</section>',start)","existing=s.find('<section class=\"investment chapter\"'); boundary=s.find('<section class=\"collection chapter collection-legacy\"',existing)\nif existing>=0 and boundary>=0:s=s[:existing]+s[boundary:]\nstart=s.index('<div id=\"actualidad\"');end=s.index('</section>',start)")
s=s.replace("s=s.replace('</body>','<script src=\"investment.js?v=1\" defer></script></body>')","\nif 'src=\"investment.js?' not in s:s=s.replace('</body>','<script src=\"investment.js?v=1\" defer></script></body>')")
p.write_text(s)
