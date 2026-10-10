"""Validated local public-data projection of the isolated DEV Commerce Engine."""
from pathlib import Path
import json,os
PATH=Path("/Users/kyouhan/AIControlCenterRuntime/dev-order/data/product-projection.json")

def apply_projection(records,data,catalog_hash,environment="DEV"):
    if data.get("schema_version")!=1 or data.get("environment")!=environment or data.get("catalog_sha256")!=catalog_hash:
        raise ValueError("DEV_PRODUCT_PROJECTION_BOUNDARY")
    rows=data.get("products")
    if type(rows) is not dict or set(rows)!={r["id"] for r in records}:raise ValueError("DEV_PRODUCT_PROJECTION_SCOPE")
    result=[]
    for r in records:
        row=rows[r["id"]]
        if type(row) is not dict or set(row)!={"enabled","regular_price","sale_price","inventory"}:raise ValueError("DEV_PRODUCT_PROJECTION_FIELDS")
        regular,sale=row["regular_price"],row["sale_price"]
        if type(row["enabled"]) is not bool or type(regular) is not int or not 1<=regular<=10000000 or (sale is not None and (type(sale) is not int or not 0<sale<regular)):
            raise ValueError("DEV_PRODUCT_PROJECTION_PRICE")
        inv=row["inventory"]
        if type(inv) is not dict or set(inv)!=set(r["inventory"]) or any(type(v) is not int or not 0<=v<=9999 for v in inv.values()):
            raise ValueError("DEV_PRODUCT_PROJECTION_INVENTORY")
        collections=[c for c in r.get("collections",[]) if c!="sale"]+(["sale"] if sale else [])
        result.append({**r,**row,"price":sale or regular,"collections":collections,"managed_projection":True})
    return tuple(result)

def read_projection(path,records,catalog_hash):
    path=Path(path);s=path.stat()
    if path.is_symlink() or s.st_uid!=os.getuid() or s.st_mode&0o077 or s.st_size>131072:raise ValueError("DEV_PRODUCT_PROJECTION_FILE")
    return apply_projection(records,json.loads(path.read_text()),catalog_hash,environment=os.environ.get("AICC_COMMERCE_ENV","DEV"))
