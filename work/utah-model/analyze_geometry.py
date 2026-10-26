import json,numpy as np
from pathlib import Path
p=Path(__file__).parent;d=json.loads((p/'extracted.json').read_text());transforms=[];report=[]
for i,n in enumerate(d['nodes']):
 m=np.array(n['transform']).reshape(4,4).T if n['transform'] else np.eye(4)
 if n['parent'] is not None:m=transforms[n['parent']]@m
 transforms.append(m);g=d['geometries'][n['geometry']]
 if not g['vertices']:continue
 v=np.array(g['vertices']);v=(m[:3,:3]@v.T).T+m[:3,3]
 report.append({'id':i,'name':n['name'],'parent':n['parent'],'min':v.min(0).tolist(),'max':v.max(0).tolist(),'triangles':len(g['triangles']),'materials':list(set(g['materials'])),'transform':m.tolist()})
(p/'bounds.json').write_text(json.dumps(report,indent=2))
for r in report:
 print(r['id'],r['name'],r['parent'],r['triangles'],np.round(r['min'],2),np.round(r['max'],2))
