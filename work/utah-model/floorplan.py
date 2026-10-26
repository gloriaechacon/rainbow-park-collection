exec(open('work/utah-model/analyze_geometry.py').read().split('for r in report:')[0])
import html
furn=json.loads((p/'furnishings.json').read_text());dst=Path('work/sites/r15-ocala/dist/utah');S=49
X=lambda x:145+(x-3.4)*S
Y=lambda y:170+(28-y)*S
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1150" viewBox="0 0 1200 1150"><rect width="1200" height="1150" fill="#f4f0e6"/><style>text{font-family:Arial,sans-serif;fill:#263f32}.tiny{font-size:12px}.label{font-size:12px;letter-spacing:1px}.dim{font-size:15px}</style><text x="74" y="56" font-size="12" letter-spacing="3">RAINBOW PARK COLLECTION / NEXT FRAGA REAL ESTATE</text><text x="74" y="112" font-size="42" style="font-family:Georgia">Utah. Una planta, muchas posibilidades.</text>']
world={}
for r in report:
 i=r['id'];n=d['nodes'][i];geo=d['geometries'][n['geometry']];v=np.array(geo['vertices']);m=np.array(r['transform']);v=(m[:3,:3]@v.T).T+m[:3,3];world[i]=(v,np.array(geo['triangles']))
v,faces=world[73]
for tri in v[faces]:
 if np.all(np.abs(tri[:,2]-.25)<.001):svg.append('<polygon points="'+' '.join(f'{X(x):.2f},{Y(y):.2f}' for x,y,z in tri)+'" fill="#fffdf7"/>')
for o in furn:
 if o['kind'] not in ['furniture','kitchen','bath']:continue
 x,y,z=o['position'];w,depth,h=o['size'];svg.append(f'<rect x="{X(x-w/2):.2f}" y="{Y(y+depth/2):.2f}" width="{w*S:.2f}" height="{depth*S:.2f}" rx="3" fill="{o["color"]}" stroke="#aaa58e" stroke-width=".65" opacity=".65"/>')
wallids=set(range(74,112))|set(range(136,141))|{166,167}
for i,(v,faces) in world.items():
 if i in [165,168,169,170]:continue
 seg=[]
 for tri in v[faces]:
  pts=[]
  for a,b in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:
   if (a[2]-1.45)*(b[2]-1.45)<0:pts.append(a+(b-a)*(1.45-a[2])/(b[2]-a[2]))
  if len(pts)==2:seg.append([tuple(np.round(q[:2],5)) for q in pts])
 if i in wallids:
  while seg:
   a,b=seg.pop();chain=[a,b]
   for _ in range(len(seg)+1):
    found=next((j for j,s in enumerate(seg) if chain[-1] in s),None)
    if found is None:break
    s=seg.pop(found);chain.append(s[1] if s[0]==chain[-1] else s[0])
    if chain[-1]==chain[0]:break
   svg.append('<path d="M'+' L'.join(f'{X(x):.2f},{Y(y):.2f}' for x,y in chain)+' Z" fill="#304839" stroke="#304839" stroke-width=".8"/>')
 else:
  for a,b in seg:svg.append(f'<path d="M{X(a[0]):.2f},{Y(a[1]):.2f} L{X(b[0]):.2f},{Y(b[1]):.2f}" fill="none" stroke="#667363" stroke-width=".9"/>')
labels=[(6.9,17.3,'GARAJE'),(10.9,16,'SALA'),(10.2,21.85,'COCINA'),(12.15,19.3,'COMEDOR'),(14.8,13.6,'DORM. 01'),(18.8,14.2,'DORM. 02'),(18.7,19.1,'DORM. 03'),(7.3,24.5,'DORM. / ANEXO'),(7.8,23.1,'ESTANCIA ANEXO'),(6.9,20.9,'LAVADO'),(15.3,20.7,'BAÑO'),(10.3,25.1,'BAÑO')]
for x,y,t in labels:svg.append(f'<text x="{X(x)}" y="{Y(y)}" text-anchor="middle" class="label">{t}</text>')
x1,x2=X(3.816271),X(20.567729);y=Y(11.55);svg.append(f'<path d="M{x1},{y-13}V{y+13} M{x1},{y}H{x2} M{x2},{y-13}V{y+13}" stroke="#63755d" fill="none"/><text x="{(x1+x2)/2}" y="{y+27}" text-anchor="middle" class="dim">16.75 m · envolvente de la base</text>')
x=X(22);y1,y2=Y(27.440275),Y(12.953737);svg.append(f'<path d="M{x-13},{y1}H{x+13} M{x},{y1}V{y2} M{x-13},{y2}H{x+13}" stroke="#63755d" fill="none"/><text transform="translate({x+28},{(y1+y2)/2}) rotate(90)" text-anchor="middle" class="dim">14.49 m · envolvente de la base</text>')
svg.append('<text x="74" y="1060" font-size="21">169.53 m² de losa modelada</text><text x="74" y="1088" class="tiny">Geometría y sección extraídas del SketchUp. Usos, mobiliario y acabados propuestos para revisión.</text><text x="74" y="1110" class="tiny">Incluye las áreas de la losa del archivo. No es superficie habitable certificada ni plano constructivo.</text></svg>');(dst/'floorplan.svg').write_text(''.join(svg));print('floorplan ready')
