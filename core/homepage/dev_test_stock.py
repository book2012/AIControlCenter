"""Explicit DEV-only inventory overlay; never claims real stock or restocks on replay."""
from pathlib import Path
import hashlib,json
PATH=Path(__file__).resolve().parents[2]/'brands/agachichi/catalog/dev-test-stock.json'
def overlay(records,source,path=PATH):
    data=json.loads(Path(path).read_text())
    if data.get('environment')!='DEV' or data.get('schema_version')!=1 or data.get('status')!='USER_AUTHORIZED_TEST_INVENTORY' or data.get('catalog_sha256')!=hashlib.sha256(Path(source).read_bytes()).hexdigest():
        raise ValueError('DEV_TEST_STOCK_BOUNDARY')
    pending={r['id']:r for r in records if r.get('inventory_pending') is True}
    if type(data.get('products')) is not dict or set(data['products'])!=set(pending):raise ValueError('DEV_TEST_STOCK_SCOPE')
    result=[]
    for row in records:
        if row['id'] not in pending:result.append(row);continue
        spec=data['products'][row['id']]
        expected=['FREE'] if row['category'] in ['bag','acc'] else ['S','M','L']
        if spec.get('sizes')!=expected or type(spec.get('quantity_per_combination')) is not int or spec['quantity_per_combination']!=3:raise ValueError('DEV_TEST_STOCK_OPTIONS')
        inventory={c['id']+'--'+size.lower():3 for c in row['color_options'] for size in expected}
        result.append({**row,'option_type':'color_size','size_options':expected,'inventory':inventory,'inventory_pending':False,'inventory_test':True})
    return tuple(result)
