import json,math,pathlib
p=pathlib.Path('work/confirmed-lots');raw=json.loads((p/'pins-and-parcels-roads.json').read_text())
def closest(pt,a,b):
 dx,dy=b[0]-a[0],b[1]-a[1]; t=max(0,min(1,((pt[0]-a[0])*dx+(pt[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
 q=[a[0]+t*dx,a[1]+t*dy];return math.dist(pt,q),q

def center(ring):
 x0,y0=ring[0];xy=[[x-x0,y-y0] for x,y in ring];ar=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(xy,xy[1:]))/2
 cx=sum((a[0]+b[0])*(a[0]*b[1]-b[0]*a[1]) for a,b in zip(xy,xy[1:]))/(6*ar)
 cy=sum((a[1]+b[1])*(a[0]*b[1]-b[0]*a[1]) for a,b in zip(xy,xy[1:]))/(6*ar)
 return [cx+x0,cy+y0],abs(ar)

out=[]
for i,v in enumerate(raw,1):
 f=v['intersections']['features'][0];nf=v['parcelNative']['features'][0];attrs=f['attributes'];wring=f['geometry']['rings'][0];ring=nf['geometry']['rings'][0];c,area=center(ring);wc,_=center(wring)
 edges=[]
 for j,(a,b) in enumerate(zip(ring,ring[1:])):
  m=[(a[0]+b[0])/2,(a[1]+b[1])/2]; near=[]
  for road in v['roadsNative'].get('features',[]):
   for path in road['geometry']['paths']:
    ds=[closest(m,a,b) for a,b in zip(path,path[1:])]
    if ds:
     d,pt=min(ds,key=lambda s:s[0]); near.append((d,road['attributes']['STREET'],pt))
  d,street,roadpt=min(near,key=lambda s:s[0]);length=math.dist(a,b)
  # Use outward edge-normal (not center-to-segment vector, which skews grouped parcels).
  n=[b[1]-a[1],-(b[0]-a[0])]
  if n[0]*(m[0]-c[0])+n[1]*(m[1]-c[1])<0:n=[-n[0],-n[1]]
  gridbear=(math.degrees(math.atan2(n[0],n[1]))+360)%360
  # Geographic normal from the same edge in WGS84, oriented by outward grid normal.
  wa,wb=wring[j],wring[j+1];dx=(wb[0]-wa[0])*math.cos(math.radians(wc[1]));dy=wb[1]-wa[1];gn=[dy,-dx]
  if gn[0]*n[0]+gn[1]*n[1]<0:gn=[-gn[0],-gn[1]]
  bearing=(math.degrees(math.atan2(gn[0],gn[1]))+360)%360
  edges.append({'index':j,'coordinates':[wa,wb],'lengthFt':round(length,2),'nearestStreet':street,'roadCenterlineDistanceFt':round(d,2),'frontBearingDegrees':round(bearing,2),'gridFrontBearingDegrees':round(gridbear,2)})
 # User requests the ~76ft side along the street. For the combined parcel, keep its whole boundary and use the closest road-facing constituent edge only as a bearing reference.
 candidates=[e for e in edges if 65<=e['lengthFt']<=85]
 front=min(candidates or edges,key=lambda e:e['roadCenterlineDistanceFt'])
 depth=sorted([e['lengthFt'] for e in edges if e['lengthFt']>100])
 depth=sum(depth)/len(depth) if depth else None
 d={'id':f'RP-{i:02d}','pinIndex':i,'sourceURL':v['source'],'resolvedURL':v['resolved'],'pin':v['pin'],'parcelId':attrs['PARCEL'],'parcelPolygon':{'type':'Polygon','coordinates':f['geometry']['rings']},'center':{'lat':wc[1],'lon':wc[0]},'countyAcres':attrs['ACRES'],'countyZoning':attrs['ZONE1'],'countyResidentialBuildings':attrs['RESBLDS'],'gisAreaSqFt':round(area,2),'gisAreaAcres':round(area/43560,4),'front':front,'depthFtApprox':round(depth,2) if depth else None,'edges':edges,'precision':'Polígono catastral oficial; coincide con el pin aportado. No es un levantamiento topográfico.','source':'Marion County GIS / Marion County Property Appraiser','parcelSourceURL':v['parcelQueryURL'],'roadsSourceURL':v['roadQueryURL'],'frontBasis':'Lado de unos 76ft más próximo a la línea central de una calle en el GIS oficial. Orientación estimada, sujeta al acceso y levantamiento final.','inventoryStatus':'Ubicación aportada por el cliente; disponibilidad comercial y titularidad no verificadas','countyAlternateKey':nf['attributes']['ALT_Key']}
 if i==10:
  d['groupedParcel']=True;d['possibleLotCount']=3;d['needsConfirmation']='El catastro agrupa 0.70 acres en una sola parcela con geometría aproximada 225 × 135ft y tres tramos de frente de unos75ft. Puede explicar los13lotes indicados con11pins. No se han confirmado los números de lotes originales ni límites internos; conservar contorno conjunto hasta confirmación.'
 out.append(d)
result={'asOf':'2026-10-13','coordinateSystem':'EPSG:4326','sourceParcelCRS':'EPSG:2237, US survey feet','userReportedLotCount':13,'providedPinCount':11,'matchedCountyParcelCount':11,'summary':'11 pins resueltos; cada pin intersecta exactamente una parcela oficial distinta. 1 parcela de0.24ac,9 de0.23ac y1 agrupada de0.70ac. La agrupada puede equivaler a3lotes originales, pendiente de confirmar.','sources':{'parcels':'https://gis.marionfl.org/public/rest/services/General/ParcelsAndSubdivisions/MapServer/0','streets':'https://gis.marionfl.org/public/rest/services/General/Streets/MapServer/0'},'lots':out}
(p/'confirmed-lot-geography.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
(p/'confirmed-parcels.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':d['parcelPolygon'],'properties':{k:d[k] for k in ['id','pinIndex','parcelId','countyAcres','countyZoning']}} for d in out]},ensure_ascii=False,indent=2))
for d in out:print(d['id'],d['parcelId'],d['countyAcres'],d['gisAreaSqFt'],d['front']['nearestStreet'],d['front']['lengthFt'],d['front']['roadCenterlineDistanceFt'],d['front']['frontBearingDegrees'],d['depthFtApprox'])
