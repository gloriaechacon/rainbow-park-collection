import json
from pathlib import Path
b=Path(__file__).parent
f=[]
def box(name,x,y,z,w,d,h,color,kind='detail'):
 f.append({'name':name,'position':[x,y,z],'size':[w,d,h],'color':color,'kind':kind})
# All locations in the original SketchUp coordinates, metres. Furnishing is a new design proposal.
for i,(x,y,w,d) in enumerate([(14.85,14.65,1.5,2),(18.8,15.3,1.6,2),(18.8,20.7,1.6,2),(7.25,26,1.8,2)]):
 box('Cama / base',x,y,.43,w+.08,d+.08,.28,'#ae9473','furniture');box('Colchón lino',x,y,.64,w,d,.25,'#e8dfcb','furniture');box('Cabecero roble',x,y+d/2+.07,.95,w+.14,.1,1.05,'#a28c6c','furniture');box('Manta salvia',x,y-.42,.79,w,1,.035,'#85907b','furniture')
 for dx in [-w*.25,w*.25]:box('Almohada',x+dx,y+.6,.83,w*.41,.42,.15,'#f1ebdf','furniture')
 for dx in [-w/2-.32,w/2+.32]:box('Mesa de noche',x+dx,y+.67,.49,.45,.48,.48,'#b6a17e','furniture')
# Kitchen along the left edge of the social space; decorative configuration for review.
for y in [19.0,19.6,20.2,20.8,21.4]:
 box('Mueble cocina roble',9.02,y,.66,.61,.59,.82,'#ad9572','kitchen');box('Encimera piedra',9.02,y,1.09,.65,.6,.04,'#e8e4d8','kitchen')
box('Refrigerador',9.05,18.1,1.22,.68,.68,1.94,'#69716a','kitchen');box('Isla cocina',10.8,20.45,.67,.88,1.85,.84,'#b49a77','kitchen');box('Isla piedra',10.8,20.45,1.11,.98,1.95,.06,'#eee9db','kitchen');box('Placa cocción',9.03,20.2,1.12,.49,.5,.02,'#27342f','kitchen');box('Fregadero',9.03,21.15,1.115,.4,.42,.018,'#7c8988','kitchen')
for y in [19.95,20.75]:box('Taburete',11.67,y,.65,.42,.42,.72,'#8c765b','furniture')
# Living area keeps an open route from the entrance.
box('Alfombra salón',10.76,17.17,.265,3.2,2.8,.025,'#c4ba9f','furniture');box('Sofá base',9.22,17.12,.52,.84,2.25,.38,'#c6c5ae','furniture');box('Sofá respaldo',8.84,17.12,.88,.2,2.25,.8,'#b2b79d','furniture')
for y in [16.39,17.12,17.85]:box('Cojín sofá',9.2,y,.78,.7,.7,.18,'#d1d1bc','furniture')
box('Mesa de centro',10.74,17.13,.52,.8,1.1,.4,'#a08a69','furniture');box('Mueble TV',12.86,16.12,.51,.35,1.35,.45,'#ae9875','furniture');box('Pantalla',13.02,16.12,1.35,.04,1.2,.7,'#202e2b','furniture')
box('Mesa comedor',12.35,20.8,.98,1.18,1.65,.07,'#b39b78','furniture')
for x in [11.53,13.17]:
 for y in [20.3,21.3]:box('Silla comedor',x,y,.54,.45,.48,.57,'#88917c','furniture')
# Bathroom fittings are illustrative, not existing fixtures from the SKP.
for x,y in [(15.35,21.5),(10.47,26.4)]:
 box('Mueble baño',x,y,.68,.95,.46,.84,'#bca483','bath');box('Lavamanos',x,y,1.13,.78,.4,.1,'#e9e9df','bath');box('Espejo',x,y+.23,1.76,.86,.025,.95,'#a0bbb8','bath')
for x,y in [(14.7,19.4),(10.15,25.35)]:box('Sanitario ilustrativo',x,y,.5,.4,.65,.5,'#f2efe6','bath')
box('Lavadora',5.75,21.58,.71,.65,.62,.9,'#d7d9d0','furniture');box('Secadora',6.47,21.58,.71,.65,.62,.9,'#d7d9d0','furniture')
# Exterior finish accents, paving and restrained landscape.
for x in [11.8,11.91,12.02,12.13,12.24,12.35,12.46,12.57,12.68,12.79,12.9,13.01]:box('Listón acceso',x,15.11,1.51,.055,.055,2.52,'#927353','exterior')
box('Acceso piedra',12.42,13.84,.19,1.85,2.55,.12,'#ccc8b7','exterior');box('Entrada vehículo',6.91,9.1,.04,3.35,9.15,.12,'#b9b6a6','site')
for x,y in [(9.3,13.6),(10.3,13.6),(14.7,12.3),(15.7,12.3),(18.3,13.05),(19.3,13.05)]:box('Jardinera',x,y,.21,.8,.48,.26,'#aaa48a','exterior')
(b/'furnishings.json').write_text(json.dumps(f,indent=2));print(len(f),'new detail objects')
