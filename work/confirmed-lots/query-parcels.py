import urllib.request,urllib.parse,json,pathlib,concurrent.futures
p=pathlib.Path('work/confirmed-lots');a=json.loads((p/'resolved-links.json').read_text());base='https://gis.marionfl.org/public/rest/services/General/ParcelsAndSubdivisions/MapServer/0/query'
def one(v):
 q=urllib.parse.parse_qs(urllib.parse.urlparse(v['resolved']).query)['q'][0];lat,lon=map(float,q.split(','));v['pin']={'lat':lat,'lon':lon,'basis':'Coordenadas del pin: parámetro q en redirección Google Maps; no centro de cámara'}
 params={'f':'json','geometry':json.dumps({'x':lon,'y':lat,'spatialReference':{'wkid':4326}}),'geometryType':'esriGeometryPoint','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'PARCEL,ACRES,ZONE1,SITUS_1,SITUS_2,BLDS,RESBLDS,PC','returnGeometry':'true','outSR':4326}
 u=base+'?'+urllib.parse.urlencode(params)
 try:
  r=json.load(urllib.request.urlopen(u,timeout=30));v['parcelQueryURL']=u;v['intersections']=r
  if not r.get('features'):
   params['distance']=30;params['units']='esriSRUnit_Meter';u=base+'?'+urllib.parse.urlencode(params);v['nearbyQueryURL']=u;v['nearby']=json.load(urllib.request.urlopen(u,timeout=30))
 except Exception as e:v['parcelError']=str(e)
 return v
a=list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(one,a))
(p/'pins-and-parcels-raw.json').write_text(json.dumps(a,indent=2))
for i,v in enumerate(a,1):print(i,v['pin'],[f['attributes'] for f in v.get('intersections',{}).get('features',[])], 'nearby',[f['attributes'] for f in v.get('nearby',{}).get('features',[])])
