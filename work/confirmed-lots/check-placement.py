from pathlib import Path
import json,math
D=Path('work/sites/r15-ocala/dist');lots=json.loads((D/'assets/geography/collection-lots.json').read_text())['lots'];u=json.loads((D/'utah/metadata-plan-v3.json').read_text());b=json.loads((D/'bell/metadata.json').read_text());out=[]
for l in lots:
 lon0,lat0=l['center']['lon'],l['center']['lat'];rad=math.pi/180;R=6378137
 def xy(ll):return[(ll[0]-lon0)*rad*R*math.cos(lat0*rad),(ll[1]-lat0)*rad*R]
 poly=[xy(p)for p in(l.get('visualPolygon')or l['parcelPolygon'])['coordinates'][0]]
 front=[xy(p)for p in l['front']['coordinates']];mid=[sum(p[i]for p in front)/2 for i in[0,1]];B=l['front']['frontBearingDegrees']*rad;v=[math.sin(B),math.cos(B)];right=[-math.cos(B),math.sin(B)]
 def inside(x,y):
  ans=False
  for (ax,ay),(bx,by)in zip(poly,poly[1:]+poly[:1]):
   if (ay>y)!=(by>y)and x<(bx-ax)*(y-ay)/(by-ay)+ax:ans=not ans
  return ans
 for name,frontz,contour in [('Utah',7.24626,u['geometry_footprint']['contours_xz'][0]),('Bell',5.2324,b['footprint_polygon_xz_m'])]:
  origin=[mid[i]-v[i]*(6+frontz)for i in[0,1]]
  vertices=[[origin[i]+right[i]*x+v[i]*z for i in[0,1]]for x,z in contour]
  outside=sum(not inside(*p)for p in vertices)
  out.append({'lot':l['id'],'house':name,'frontStreet':l['front']['nearestStreet'],'facingBearing':l['front']['frontBearingDegrees'],'baseVerticesOutsideDisplayPolygon':outside,'boundary': 'illustrative'if l.get('provisionalBoundary')else'county GIS'})
print('Placement audit:',len(out),'house/lot combinations;',sum(x['baseVerticesOutsideDisplayPolygon'] for x in out),'vertices outside reference shapes.')
Path('outputs/collection-update/placement-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
