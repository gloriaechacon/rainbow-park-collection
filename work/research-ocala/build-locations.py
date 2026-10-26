import json,pathlib
p=pathlib.Path('work/research-ocala')
cs={r['id']:r for r in json.loads((p/'geocoder-evidence.json').read_text())}
a1={r['id']:r for r in json.loads((p/'arcgis-geocoder-evidence.json').read_text())}
a2={r['id']:r for r in json.loads((p/'arcgis-geocoder-evidence-2.json').read_text())}
def census(id,name,source,basis):
 r=cs[id];m=r['data']['result']['addressMatches'][0];c=m['coordinates']
 return dict(id=id,name=name,lat=round(c['y'],6),lon=round(c['x'],6),precision='Dirección aproximada sobre la vía',sourceURL=source,geocoderURL=r['url'],basis=basis+' Coordenada interpolada del US Census Geocoder, no centro ni lindero del predio.',matchedAddress=m['matchedAddress'])
def arcgis(id,key,name,source,basis,precision='Dirección aproximada'):
 r=(a1|a2)[key];m=r['data']['candidates'][0];c=m['location']
 return dict(id=id,name=name,lat=round(c['y'],6),lon=round(c['x'],6),precision=precision,sourceURL=source,geocoderURL=r['url'],basis=basis,matchedAddress=m['address'])
rows=[
 census('classic-mile','Classic Mile','https://www.ocala-news.com/2024/07/19/700-acre-horse-park-bought-by-wec-owners-for-nearly-27-million/','13750 W Highway 40 publicado en el reporte de la adquisición.'),
 arcgis('wec-deportivo','wec-sports','Expansión deportiva del WEC','https://www.marionfl.org/agencies-departments/departments-facilities-offices/growth-services/planning-zoning/wec-application-2026','Intersección SR 40 / NW 100th Avenue como referencia del extremo suroeste del sector del proyecto. El complejo se propone al norte de SR 40, hacia NW 80th. No es una huella de edificio ni el centro del predio. Esri devuelve StreetInt con puntuación 100.','Intersección de referencia del sector'),
 arcgis('wec-hospitalidad','manor-address','The Equestrian Manor / Shoppes Off 80th','https://worldequestriancenter.com/growth/','Punto de referencia en 8050 NW 17th Pl (The Equestrian Manor); Shoppes Off 80th anunciado junto al Manor y Riding Academy. Esri devuelve PointAddress con puntuación 100. Marcador compartido del conjunto, no ubicación de cada tienda.','Referencia del conjunto de hospitalidad'),
 census('eone','E-ONE: expansión industrial','https://ocala.legistar.com/LegislationDetail.aspx?GUID=EC7BFE32-964A-4829-A62F-BEA3634DA049&ID=7996104&Options=&Search=','Dirección de campus del expediente municipal: 2929 SW 57th Avenue.'),
 arcgis('i75-norte','i75-norte','I-75: corredor norte','https://www.cflroads.com/project/452074-1','Intersección de I-75 y SR 40 / W Silver Springs Boulevard dentro del tramo SR 200–SR 326. Esri devuelve StreetInt. Es un punto representativo de la obra, no su extensión.','Intersección representativa del corredor'),
 dict(id='nw49',name='Nuevo enlace I-75 / NW 49th Street',lat=29.237809,lon=-82.190006,precision='Punto medio del tramo mostrado por FDOT',sourceURL='https://www.cflroads.com/project/435209-1',basis='Promedio de los dos puntos de pathCoordinates del mapa oficial de FDOT: (29.2383909,-82.189999), (29.2372262,-82.190012). Representa la localización del intercambiador; no sus límites de obra.'),
 census('heathbrook','AdventHealth Heathbrook ER','https://www.adventhealth.com/news/adventhealth-cuts-ribbon-new-freestanding-emergency-department-meant-bring-faster-expert-emergency','3941 SW College Road, dirección publicada por AdventHealth el 8 de enero de 2026.'),
 census('medical-office','AdventHealth: edificio de especialidades','https://www.adventhealth.com/news/adventhealth-ocala-celebrates-grand-opening-new-medical-office-building','1219 South Pine Avenue, dirección publicada por AdventHealth el 12 de junio de 2025.'),
 arcgis('i75-sur','i75-sur','I-75: conexión hacia el sur','https://www.cflroads.com/project/452074-2','Intersección I-75 / SR 200 (SW College Road), límite norte del corredor de 23 millas que llega al sur de SR 44. Esri devuelve StreetInt. Punto representativo, no centro de toda la intervención.','Extremo norte del corredor'),
 census('smokey-willow','Smokey Willow Farm','https://www.ocala-news.com/2025/12/15/wec-owners-purchase-ocala-horse-farm-for-7-5-million/','2599 NW 100th Avenue según el reporte de adquisición.'),
 arcgis('jockey-club','jockey-club','Ocala Jockey Club','https://www.jumpmediallc.com/news/World_Equestrian_Center_Acquires_Iconic_Ocala_Jockey_Club_Property-08-05-2021/3728','8720 W Highway 318, Reddick. Esri devuelve PointAddress con puntuación 100. Situado en el norte de Marion County; fuera del entorno inmediato de Rainbow Park.','Dirección aproximada del acceso')
]
rows[2]['projectIds']=['manor','shoppes']
rows[2]['addressSourceURL']='https://starwinelist.com/wine-place/genievieves'
for r in rows:r.setdefault('projectIds',[r['id']])
result={'asOf':'2026-10-13','coordinateSystem':'WGS84 / EPSG:4326','mapNote':'Ubicaciones de referencia para explorar el entorno regional. Los marcadores identifican direcciones, accesos o intersecciones; no representan linderos de los proyectos.','locations':rows,'linework':{'file':'fdot-corridors.json','source':'Coordenadas públicas de los mapas oficiales de cada proyecto FDOT','usage':'Se pueden dibujar las líneas provistas como trazado orientativo; no convertirlas en polígonos de propiedad.'},'rejectedResults':['La búsqueda genérica World Equestrian Center en Esri devolvió el centro urbano de Ocala: descartada.','I-75 & NW 49th St se interpretó como número de casa 75: descartado. Se sustituyó por geometría oficial FDOT.','NW 49th St & NW 35th Ave devolvió calles invertidas: descartado.']}
(p/'project-locations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('Wrote',len(rows),'locations')
