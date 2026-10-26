import urllib.request,urllib.parse,json,math,pathlib,concurrent.futures,io
from PIL import Image
P=pathlib.Path('work/sites/r15-ocala/dist/assets/geography');W=4000;H=3500;lon=-82.373;lat=29.15;R=6378137;scale=math.cos(math.radians(lat));cx=R*math.radians(lon);cy=R*math.log(math.tan(math.pi/4+math.radians(lat)/2));bbox=[cx-W/2/scale,cy-H/2/scale,cx+W/2/scale,cy+H/2/scale];bboxS=','.join(str(x) for x in bbox)
baseDEM='https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer'
baseImagery='https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer'
def get(url,params=None):
 if params:url+='?'+urllib.parse.urlencode(params)
 return url,urllib.request.urlopen(url,timeout=90).read()
def imagery():
 u,data=get(baseImagery+'/export',{'bbox':bboxS,'bboxSR':3857,'imageSR':3857,'size':'4096,3584','format':'jpg','f':'json'})
 j=json.loads(data)
 if 'error' in j:raise RuntimeError(j)
 _,data=get(j['href']);img=Image.open(io.BytesIO(data));img.verify();(P/'collection-aerial.jpg').write_bytes(data)
 print('imagery',len(data),j['width'],j['height'],j['extent'],flush=True)
 return {'request':u,'response':j}
def dem():
 u,data=get(baseDEM+'/exportImage',{'bbox':bboxS,'bboxSR':3857,'imageSR':3857,'size':'512,448','format':'tiff','pixelType':'F32','interpolation':'RSP_BilinearInterpolation','renderingRule':json.dumps({'rasterFunction':'None'}),'f':'json'})
 j=json.loads(data)
 if 'error' in j:raise RuntimeError(j)
 _,data=get(j['href']);im=Image.open(io.BytesIO(data));vals=list(im.getdata());valid=[v for v in vals if math.isfinite(v) and -100<v<500];
 if len(valid)!=len(vals):raise RuntimeError(f'DEM invalid values: {len(vals)-len(valid)}')
 d={'width':im.width,'height':im.height,'values':[round(v,2) for v in vals],'min':min(vals),'max':max(vals),'source':'USGS 3DEP Bare Earth DEM','url':baseDEM,'retrieved':'2026-10-13','extent':j['extent'],'note':'Grid sampled at approximately 7.8 m across a 4000 × 3500 m area. Values are metres at true vertical scale; source vertical datum retained. Not a parcel survey.','imageRequest':u}
 (P/'collection-elevation.json').write_text(json.dumps(d,separators=(',',':')));pathlib.Path('work/confirmed-lots/collection-dem-source.tif').write_bytes(data)
 print('dem',im.size,min(vals),max(vals),flush=True)
 return {'request':u,'response':j}
def roads():
 u,data=get('https://gis.marionfl.org/public/rest/services/General/Streets/MapServer/0/query',{'f':'json','geometry':bboxS,'geometryType':'esriGeometryEnvelope','inSR':3857,'spatialRel':'esriSpatialRelIntersects','outFields':'STREET,ROAD_TYPE,CLASS','returnGeometry':'true','outSR':3857})
 j=json.loads(data)
 if 'error' in j:raise RuntimeError(j)
 if j.get('exceededTransferLimit'):raise RuntimeError('Road query needs paging')
 out=[]
 for f in j['features']:
  at=f['attributes'];name=at.get('STREET','');kind='primary' if 'HWY 40' in name or 'HIGHWAY 40' in name else 'residential'
  for path in f['geometry']['paths']:
   out.append({'name':name,'kind':kind,'points':[[round((x-cx)*scale,2),round((cy-y)*scale,2)] for x,y in path]})
 print('roads',len(out),flush=True)
 return out,u
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 fs=[pool.submit(imagery),pool.submit(dem),pool.submit(roads)];im=fs[0].result();de=fs[1].result();rd,ru=fs[2].result()
context={'center':[lon,lat],'width':W,'height':H,'projection':'Local Web Mercator scaled at center latitude; units metres','roads':rd,'sources':{'imagery':'USDA / USGS The National Map, imagery date at this location unverified','roads':'Marion County GIS Streets — official public road centerlines','roadsURL':ru,'retrieved':'2026-10-13','imageRequest':im['request']},'extent':im['response']['extent']}
(P/'collection-context.json').write_text(json.dumps(context,separators=(',',':')))
pathlib.Path('work/confirmed-lots/collection-terrain-provenance.json').write_text(json.dumps({'center':[lon,lat],'width':W,'height':H,'bbox3857':bbox,'imagery':im,'dem':de,'roadsURL':ru},indent=2))
print('DONE',flush=True)
