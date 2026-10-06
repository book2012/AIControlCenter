# Manifest-bound DEV gallery; uploaded photos and AI illustrations stay separate.
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/'brands/agachichi/assets/media/uploads/gallery.json'
def assets():
    try:
        payload=json.loads(MANIFEST.read_text())
        if payload.get('environment')!='DEV' or payload.get('schema_version')!=1:return {}
        result={}
        base=ROOT/'brands/agachichi/assets/media/uploads/gallery'
        for row in payload['assets']:
            pid=row['product_id'];kind=row['kind']
            if not re.fullmatch(r'ag-upload-outer-[0-9]{4}',pid) or kind not in {'original','model-angles'}:return {}
            name=pid+'-'+kind+'.jpg';path=base/name
            if row['path']!=str(path.relative_to(ROOT)) or path.is_symlink() or not path.is_file():return {}
            if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:return {}
            if type(row['ai_generated']) is not bool or row['ai_generated']!=(kind=='model-angles'):return {}
            if name in result:return {}
            result[name]={**row,'path':path,'url':'/homepage/assets/storefront/gallery/'+name}
        return result
    except (OSError,ValueError,KeyError,TypeError):return {}
def for_product(pid):
    return [row for row in assets().values() if row['product_id']==pid]
