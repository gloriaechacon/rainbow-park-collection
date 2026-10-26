import urllib.request,urllib.parse,json,pathlib,concurrent.futures
p=pathlib.Path('work/confirmed-lots');a=json.loads((p/'pins-and-parcels-raw.json').read_text())
def query(url,params):
 u=url+'?'+urllib.parse.urlencode(params);return u,json.load(urllib.request.urlopen(u,timeout=30))
def one(v):
 lat,lon=v['pin']['lat'],v['pin']['lon'];geom=json.dumps({'x':lon,'y':lat,'spatialReference':{'wkid':4326}})
 params={'f':'json','geometry':geom,'geometryType':'esriGeometryPoint','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'STREET,ROAD_TYPE,RESP_MAINT,CLASS','returnGeometry':'true','outSR':2237,'distance':90,'units':'esriSRUnit_Meter'}
 v['roadQueryURL'],v['roadsNative']=query('https://gis.marionfl.org/public/rest/services/General/Streets/MapServer/0/query',params)
 parcelid=v['intersections']['features'][0]['attributes']['PARCEL']
 params={'f':'json','where':"PARCEL='"+parcelid+"'",'outFields':'PARCEL,ACRES,ZONE1,SITUS_1,SITUS_2,BLDS,RESBLDS,PC,ALT_Key','returnGeometry':'true','outSR':2237}
 v['parcelNativeQueryURL'],v['parcelNative']=query('https://gis.marionfl.org/public/rest/services/General/ParcelsAndSubdivisions/MapServer/0/query',params)
 return v
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(one,a));(p/'pins-and-parcels-roads.json').write_text(json.dumps(r,indent=2))
for i,v in enumerate(r,1):print(i,v['parcelNative']['features'][0]['attributes'],[f['attributes'] for f in v['roadsNative'].get('features',[])])
