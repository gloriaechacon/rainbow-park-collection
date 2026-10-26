from pathlib import Path
import json
root=Path('work/model-finishes');sources=(root/'translatable.txt').read_text().splitlines();catalog={}
for file in ['translations.tsv','translations-extra.tsv']:
    for line in (root/file).read_text().splitlines():
        if not line.strip():continue
        key,en,pt=line.split('|');es=sources[int(key)] if key.isdigit() else key
        catalog[es]=[en,pt]
target=Path('work/sites/r15-ocala/dist/locales');target.mkdir(exist_ok=True)
(target/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':')))
print(len(catalog),'translations per language')
