import urllib.request,urllib.parse,json,pathlib,concurrent.futures
p=pathlib.Path('work/confirmed-lots');raw=json.loads((p/'pins-and-parcels-roads.json').read_text());byid={v['source'].split('/')[-1].split('?')[0]:v for v in raw}
order=['cv3Yk7ZEWxuJxoNZA','xHquFQMqNVojJxx1A','Z9MmDG9dsHs76Rck9','RKLdbHRtrHzyxjZ36','AzAN3xu4XMK5UDVcA','gf4cEFFMxmtkX4pr6','kf1Vbm8tcBPAC5FD6','uRu7W8AQQXxGpJZ79','mynLnMyGwMwd7Vx69','hSBR6mwFy2DesUZDA','3YU7FPiFZGgV1gmC9','QtZ1aMbaiZ57RX2T7','dkEdyTc1Uh5jeSD89']
def query(base,params):
 u=base+'?'+urllib.parse.urlencode(params);return u,json.load(urllib.request.urlopen(u,timeout=30))
def get(k):
 u='https://maps.app.goo.gl/'+k+'?g_st=ic';resp=urllib.request.urlopen(u,timeout=20);resolved=resp.url;v={'source':u,'resolved':resolved}
 coord=urllib.parse.parse_qs(urllib.parse.urlparse(resolved).query)['q'][0];lat,lon=map(float,coord.split(','));v['pin']={'lat':lat,'lon':lon,'basis':'Coordenadas del pin: parámetro q en redirección Google Maps; no centro de cámara'};geom=json.dumps({'x':lon,'y':lat,'spatialReference':{'wkid':4326}})
 params={'f':'json','geometry':geom,'geometryType':'esriGeometryPoint','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'PARCEL,ACRES,ZONE1,SITUS_1,SITUS_2,BLDS,RESBLDS,PC','returnGeometry':'true','outSR':4326}
 v['parcelQueryURL'],v['intersections']=query('https://gis.marionfl.org/public/rest/services/General/ParcelsAndSubdivisions/MapServer/0/query',params)
 parcelid=v['intersections']['features'][0]['attributes']['PARCEL']
 params={'f':'json','geometry':geom,'geometryType':'esriGeometryPoint','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'STREET,ROAD_TYPE,RESP_MAINT,CLASS','returnGeometry':'true','outSR':2237,'distance':90,'units':'esriSRUnit_Meter'}
 v['roadQueryURL'],v['roadsNative']=query('https://gis.marionfl.org/public/rest/services/General/Streets/MapServer/0/query',params)
 params={'f':'json','where':"PARCEL='"+parcelid+"'",'outFields':'PARCEL,ACRES,ZONE1,SITUS_1,SITUS_2,BLDS,RESBLDS,PC,ALT_Key','returnGeometry':'true','outSR':2237}
 v['parcelNativeQueryURL'],v['parcelNative']=query('https://gis.marionfl.org/public/rest/services/General/ParcelsAndSubdivisions/MapServer/0/query',params)
 return k,v
for k,v in concurrent.futures.ThreadPoolExecutor(max_workers=2).map(get,[k for k in order if k not in byid]):
 byid[k]=v;print(k,v['pin'],v['intersections']['features'][0]['attributes'])
r=[byid[k] for k in order];(p/'pins-and-parcels-roads-final13.json').write_text(json.dumps(r,indent=2));print('final13saved')
