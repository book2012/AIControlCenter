# Manifest-bound DEV gallery; uploaded photos and AI illustrations stay separate.
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/'brands/agachichi/assets/media/uploads/gallery.json'
def assets():
    try:
        payload=json.loads(MANIFEST.read_text())
        if payload.get('environment')!='DEV' or payload.get('schema_version')!=1:return {}
        result={};colors=None;bindings=set()
        base=ROOT/'brands/agachichi/assets/media/uploads/gallery'
        if base.is_symlink() or base.resolve()!=base.absolute():return {}
        for row in payload['assets']:
            pid=row['product_id'];kind=row['kind'];color=row.get('color_id')
            if not re.fullmatch(r'ag-upload-(top|bottom|outer|dress|bag|acc)-[0-9]{4}',pid) or kind not in {'original','model-angles','model-front','model-other','garment-cutout','color-front'}:return {}
            if color is not None or kind=='color-front':
                if kind not in {'model-front','color-front'} or not isinstance(color,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,31}',color):return {}
                if colors is None:
                    catalog=json.loads((ROOT/'brands/agachichi/catalog/dev-upload-products.json').read_text())
                    if catalog.get('environment')!='DEV' or catalog.get('schema_version')!=1:return {}
                    colors={p['id']:{v['id'] for v in p.get('color_options',[])} for p in catalog['products']}
                if color not in colors.get(pid,set()) or (pid,color) in bindings:return {}
                bindings.add((pid,color))
            name=pid+('-color-'+color if kind=='color-front' else '-'+kind)+('.webp' if kind=='garment-cutout' else '.jpg');path=base/name
            if row['path']!=str(path.relative_to(ROOT)) or path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(base.resolve()):return {}
            if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:return {}
            if type(row['ai_generated']) is not bool or row['ai_generated']!=(kind!='original'):return {}
            if name in result:return {}
            result[name]={**row,'path':path,'url':'/homepage/assets/storefront/gallery/'+name}
        return result
    except (OSError,ValueError,KeyError,TypeError):return {}
def for_product(pid):
    rows=[row for row in assets().values() if row['product_id']==pid]
    order={'garment-cutout':0,'model-other':1}
    return sorted([row for row in rows if row['kind'] in order],key=lambda row:order[row['kind']])

def front(pid):
    return assets().get(pid+'-model-front.jpg')

def color_fronts(pid):
    return {row['color_id']:row for row in assets().values() if row['product_id']==pid and row.get('color_id')}
