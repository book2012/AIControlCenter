"""Production-only registration for one validated uploaded catalog item.

Default mode is read-only. --apply-prod creates only the matching WooCommerce
product in the ai-shopping production store, with every pending variant at 0.
It stages a private binding candidate; it never changes orders or activates stock.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO))
PRIVATE = Path("/Users/kyouhan/.config/aicontrolcenter-prod-commerce")
RUNTIME = Path("/Users/kyouhan/AIControlCenterRuntime/prod-commerce")
DOCKER = ["docker", "--context", "colima-aicontrolcenter-commerce"]
WORDPRESS = "shopping-wordpress"
SKU_PREFIX = "aicc-prod-"

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None: raise RuntimeError("MODULE_UNAVAILABLE")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def private_config():
    path=PRIVATE/"runtime.private.json"
    if PRIVATE.is_symlink() or path.is_symlink() or not path.is_file() or path.stat().st_uid!=os.getuid() or path.stat().st_mode&0o077:
        raise RuntimeError("PROD_PRIVATE_CONFIGURATION_INVALID")
    value=json.loads(path.read_text())
    if value.get("environment")!="PROD" or not isinstance(value.get("bindings"),list):
        raise RuntimeError("PROD_PRIVATE_CONFIGURATION_INVALID")
    return value

def run(cmd, *, input_text=None, timeout=90):
    return subprocess.run(cmd,input=input_text,text=True,capture_output=True,timeout=timeout)

def registration_php():
    dev=load_module("dev_product_register_for_prod_php",REPO/"ops/macos/shopping/dev_upload_product_register.py")
    php=dev.PHP[5:-2].strip().replace("aicc_order_dev","aicc_shopping").replace("'DEV'","'PROD'")
    php=php.replace("/tmp/aicc-dev-product-registration/","/tmp/aicc-prod-product-registration/")
    old="""  if ($id) {
    $receipt = aicc_snapshot($id, $cfg);
    echo wp_json_encode(['environment'=>'PROD','state'=>'ALREADY_REGISTERED','order_count'=>$beforeOrders,'product'=>$receipt]);
    exit(0);
  }
"""
    new="""  if ($id) {
    $existing = wc_get_product($id);
    if ($cfg['mode'] === 'inspect' && $existing && $existing->get_status() === 'draft'
        && $existing->get_sku() === $sku && $existing->get_meta('_aicc_catalog_id') === $cfg['catalog_id']) {
      echo wp_json_encode(['environment'=>'PROD','state'=>'INCOMPLETE','sku'=>$sku,'order_count'=>$beforeOrders]); exit(0);
    }
    if (!($cfg['mode'] === 'apply' && $existing && $existing->get_status() === 'draft'
        && $existing->get_sku() === $sku && $existing->get_meta('_aicc_catalog_id') === $cfg['catalog_id'])) {
      $receipt = aicc_snapshot($id, $cfg);
      echo wp_json_encode(['environment'=>'PROD','state'=>'ALREADY_REGISTERED','order_count'=>$beforeOrders,'product'=>$receipt]);
      exit(0);
    }
  }
"""
    if old not in php:raise RuntimeError("PROD_PHP_EXISTING_PRODUCT_BLOCK_NOT_FOUND")
    php=php.replace(old,new)
    old="""  foreach ($cfg['variants'] as $variant) {
    if (wc_get_product_id_by_sku($sku . '-' . sanitize_title($variant['key']))) { throw new Exception('VARIATION_SKU_ALREADY_USED'); }
  }
  $p = new WC_Product_Variable();
"""
    new="""  foreach ($cfg['variants'] as $variant) {
    $existingVariationId=wc_get_product_id_by_sku($sku . '-' . sanitize_title($variant['key']));
    if ($existingVariationId) {
      $existingVariation=wc_get_product($existingVariationId);
      if (!$id || !$existingVariation || $existingVariation->get_parent_id() !== (int)$id) { throw new Exception('VARIATION_SKU_ALREADY_USED'); }
    }
  }
  $p = $id ? wc_get_product($id) : new WC_Product_Variable();
  if (!$p || ($id && ($p->get_status() !== 'draft' || $p->get_sku() !== $sku || $p->get_meta('_aicc_catalog_id') !== $cfg['catalog_id']))) { throw new Exception('PRODUCT_REPAIR_SCOPE'); }
"""
    if old not in php:raise RuntimeError("PROD_PHP_VARIATION_BLOCK_NOT_FOUND")
    php=php.replace(old,new)
    php=php.replace("""    $v = new WC_Product_Variation();
    $v->set_parent_id($id); $v->set_sku($sku . '-' . sanitize_title($variant['key']));
""","""    $existingVariationId=wc_get_product_id_by_sku($sku . '-' . sanitize_title($variant['key']));
    $v = $existingVariationId ? wc_get_product($existingVariationId) : new WC_Product_Variation();
    if (!$v || ($existingVariationId && $v->get_parent_id() !== (int)$id)) { throw new Exception('PRODUCT_VARIANT_REPAIR_SCOPE'); }
    $v->set_parent_id($id); $v->set_sku($sku . '-' . sanitize_title($variant['key']));
""")
    old="""  $attachmentIds = [];
  foreach ($cfg['media'] as $index=>$media) {
    $tmp = '/tmp/aicc-prod-product-registration/' . $cfg['catalog_id'] . '/asset-' . $index . $media['extension'];
"""
    new="""  $attachmentIds = [];
  $existingMedia=[];
  $existingProduct=wc_get_product($id);
  if ($existingProduct) {
    $oldIds=array_filter(array_merge([$existingProduct->get_image_id()],$existingProduct->get_gallery_image_ids()));
    foreach ($oldIds as $oldId) { $oldPath=get_attached_file($oldId); if ($oldPath && is_file($oldPath)) $existingMedia[hash_file('sha256',$oldPath)]=(int)$oldId; }
  }
  foreach ($cfg['media'] as $index=>$media) {
    if (isset($existingMedia[$media['sha256']])) { $attachmentIds[]=$existingMedia[$media['sha256']]; continue; }
    $tmp = '/tmp/aicc-prod-product-registration/' . $cfg['catalog_id'] . '/asset-' . $index . $media['extension'];
"""
    if old not in php:raise RuntimeError("PROD_PHP_MEDIA_BLOCK_NOT_FOUND")
    php=php.replace(old,new)
    php=php.replace("'order_count'=>$afterOrders,", "'order_count'=>$afterOrders,'order_count_before'=>$beforeOrders,")
    return php

def payload(product, mode):
    sku=SKU_PREFIX+product["catalog_id"]
    return {**product,"sku":sku,"environment":"PROD","mode":mode,
        "media":[{**media,"filename":Path(media["path"]).name,"extension":Path(media["path"]).suffix,
          "container_path":f"/tmp/aicc-prod-product-registration/{product['catalog_id']}/asset-{i}{Path(media['path']).suffix}"}
          for i,media in enumerate(product["media"])]}

def call_woo(product, mode):
    p=payload(product,mode)
    if mode=="apply":
        root=f"/tmp/aicc-prod-product-registration/{product['catalog_id']}"
        r=run(DOCKER+["exec",WORDPRESS,"mkdir","-p",root],timeout=30)
        if r.returncode: raise RuntimeError("PROD_MEDIA_STAGE_FAILED")
        for i,m in enumerate(product["media"]):
            r=run(DOCKER+["cp",m["path"],f"{WORDPRESS}:{root}/asset-{i}{Path(m['path']).suffix}"],timeout=40)
            if r.returncode: raise RuntimeError("PROD_MEDIA_STAGE_FAILED")
    r=run(DOCKER+["exec","-i",WORDPRESS,"php","-d","memory_limit=512M","-r",registration_php()],
          input_text=json.dumps(p,ensure_ascii=False),timeout=180 if mode=="apply" else 60)
    if r.returncode: raise RuntimeError("PROD_PRODUCT_REGISTRATION_FAILED_INSPECT_REQUIRED")
    try: out=json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: raise RuntimeError("PROD_PRODUCT_RECEIPT_INVALID") from None
    if out.get("environment")!="PROD" or not isinstance(out.get("order_count"),int):
        raise RuntimeError("PROD_PRODUCT_RECEIPT_INVALID")
    if mode=="apply" and out["order_count"]!=out.get("order_count_before"):
        raise RuntimeError("PROD_ORDER_COUNT_CHANGED")
    return out

def private_write(path,value):
    fd,tmp=tempfile.mkstemp(prefix=".prod-product-registration-",dir=path.parent)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(value,f,ensure_ascii=False,indent=2);f.write("\n");f.flush();os.fsync(f.fileno())
        os.replace(tmp,path);os.chmod(path,0o600)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def stage_binding(product, woo):
    config=private_config()
    sku=SKU_PREFIX+product["catalog_id"]
    pid=product["catalog_id"]
    bindings=config["bindings"]
    matches=[b for b in bindings if b.get("demo_id")==pid or b.get("product_id")==woo["product"]["product_id"] or b.get("sku")==sku]
    if matches and not (len(matches)==1 and matches[0].get("demo_id")==pid
        and matches[0].get("product_id")==woo["product"]["product_id"] and matches[0].get("sku")==sku):
        raise RuntimeError("PROD_PRODUCT_MAPPING_CONFLICT")
    binding={"demo_id":pid,"product_id":woo["product"]["product_id"],"sku":sku,
             "category":product["category_label"],"option_type":product["option_type"]}
    candidate=dict(config)
    cumulative=list(bindings)
    staged_candidates=[PRIVATE/"runtime.product-registration.candidate.private.json",*PRIVATE.glob("runtime.product-registration-*.candidate.private.json")]
    for staged in staged_candidates:
        if not staged.exists():continue
        if staged.is_symlink():raise RuntimeError("PROD_PRODUCT_CANDIDATE_INVALID")
        value=json.loads(staged.read_text())
        if value.get("environment")!="PROD" or not isinstance(value.get("bindings"),list):raise RuntimeError("PROD_PRODUCT_CANDIDATE_INVALID")
        for item in value["bindings"]:
            if item.get("demo_id") not in {x.get("demo_id") for x in bindings} and item.get("demo_id")!=pid:
                if not any(x.get("demo_id")==item.get("demo_id") for x in cumulative):cumulative.append(item)
    candidate["bindings"]=[b for b in cumulative if b.get("demo_id")!=pid and b.get("sku")!=sku]+[binding]
    target=PRIVATE/"runtime.product-registration.candidate.private.json"
    if target.exists():
        previous=json.loads(target.read_text())
        if previous.get("environment")!="PROD" or any(previous.get(k)!=candidate.get(k) for k in config if k!="bindings"):
            raise RuntimeError("PROD_PRODUCT_CANDIDATE_CONFLICT")
        previous_rows=previous.get("bindings",[])
        base_by_id={b.get("demo_id"):b for b in bindings}
        previous_by_id={b.get("demo_id"):b for b in previous_rows}
        if any(previous_by_id.get(k)!=v for k,v in base_by_id.items()):raise RuntimeError("PROD_PRODUCT_CANDIDATE_CONFLICT")
        extras=set(previous_by_id)-set(base_by_id)
        source_catalog=json.loads((REPO/"brands/agachichi/catalog/dev-upload-products.json").read_text())
        source_ids={row.get("id") for row in source_catalog.get("products",[])}
        for extra_id in extras:
            extra=previous_by_id[extra_id]
            if (extra_id not in source_ids or extra.get("sku")!=SKU_PREFIX+extra_id
                or not isinstance(extra.get("product_id"),int) or extra.get("product_id")<=0):
                raise RuntimeError("PROD_PRODUCT_CANDIDATE_CONFLICT")
        private_write(target,candidate)
    else:private_write(target,candidate)
    catalog=REPO/"brands/agachichi/catalog/dev-upload-products.json"
    cat=json.loads(catalog.read_text());raw=catalog.read_bytes();rows=cat["products"]
    ids={r["id"] for r in rows}
    if pid not in ids or len(ids)!=len(rows):raise RuntimeError("PROD_CATALOG_SCOPE_INVALID")
    projection_path=RUNTIME/"data/product-projection.json"
    if projection_path.is_symlink() or not projection_path.is_file() or projection_path.stat().st_mode&0o077:
        raise RuntimeError("PROD_PRODUCT_PROJECTION_INVALID")
    current=json.loads(projection_path.read_text());current_rows=current.get("products")
    if current.get("environment")!="PROD" or not isinstance(current_rows,dict):raise RuntimeError("PROD_PRODUCT_PROJECTION_INVALID")
    target_row={"enabled":True,"regular_price":product["price"],"sale_price":product["sale_price"],
                "inventory":{v["key"]:v["stock"] for v in product["variants"]}}
    new_hash=hashlib.sha256(raw).hexdigest()
    if current.get("catalog_sha256")==new_hash:
        if set(current_rows)!=ids or current_rows.get(pid)!=target_row:raise RuntimeError("PROD_PRODUCT_PROJECTION_CONFLICT")
        projected=dict(current_rows)
    else:
        if not set(current_rows).issubset(ids):raise RuntimeError("PROD_PRODUCT_PROJECTION_SCOPE_INVALID")
        projected=dict(current_rows)
        by_id={row["id"]:row for row in rows}
        for missing in sorted(ids-set(projected)):
            row=by_id[missing]
            projected[missing]={"enabled":row.get("enabled",True),"regular_price":row["price"],
                "sale_price":row.get("sale_price"),"inventory":dict(row["inventory"])}
    candidate_projection={"schema_version":1,"environment":"PROD","catalog_sha256":new_hash,"products":projected}
    proj_target=RUNTIME/"data/product-projection.candidate.json"
    if proj_target.exists() and json.loads(proj_target.read_text())!=candidate_projection:raise RuntimeError("PROD_PRODUCT_PROJECTION_CONFLICT")
    if not proj_target.exists():private_write(proj_target,candidate_projection)
    evidence={"environment":"PROD","catalog_id":pid,"product_id":woo["product"]["product_id"],
      "sku":sku,"price":product["price"],"inventory_pending":True,
      "variants":product["variants"],"images":[m["sha256"] for m in product["media"]],
      "order_count_unchanged":True,"activation":False}
    evidence_path=RUNTIME/f"product-registration-{pid}-evidence.json"
    if evidence_path.exists() and json.loads(evidence_path.read_text())!=evidence:raise RuntimeError("PROD_PRODUCT_EVIDENCE_CONFLICT")
    if not evidence_path.exists():private_write(evidence_path,evidence)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog-id",required=True)
    parser.add_argument("--apply-prod",action="store_true")
    args=parser.parse_args(argv)
    try:
        from ops.macos.shopping.prod_woo_port import assert_production
        assert_production()
        config=private_config()
        validator=load_module("prod_product_registration_validation",REPO/"core/shopping/product_registration.py")
        product=validator.validate_registration(REPO,args.catalog_id)
        product["sku"]=SKU_PREFIX+product["catalog_id"];product["environment"]="PROD"
        prior=[b for b in config["bindings"] if b.get("demo_id")==args.catalog_id]
        sku_prior=[b for b in config["bindings"] if b.get("sku")==product["sku"]]
        if prior or sku_prior:
            if len(prior)!=1 or sku_prior!=prior or prior[0].get("product_id")<1:raise RuntimeError("PROD_PRODUCT_MAPPING_CONFLICT")
            # The idempotent Woo inspect below verifies the complete binding.
        inspected=call_woo(product,"inspect")
        if inspected.get("state") not in {"SKU_AVAILABLE","ALREADY_REGISTERED","INCOMPLETE"}:raise RuntimeError("PROD_PRODUCT_REGISTRATION_STATE_INVALID")
        if not args.apply_prod:
            print(json.dumps({"environment":"PROD","catalog_id":args.catalog_id,"sku":product["sku"],
              "price":product["price"],"option_count":len(product["variants"]),
              "inventory_pending":True,"images":len(product["media"]),
              "woo_state":inspected["state"],"mutation":False},ensure_ascii=False));return 0
        result=call_woo(product,"apply") if inspected["state"] in {"SKU_AVAILABLE","INCOMPLETE"} else inspected
        if result.get("state") not in {"REGISTERED","ALREADY_REGISTERED"}:raise RuntimeError("PROD_PRODUCT_REGISTRATION_STATE_INVALID")
        stage_binding(product,result)
        print(json.dumps({"environment":"PROD","catalog_id":args.catalog_id,"sku":product["sku"],
          "state":result["state"],"product_id":result["product"]["product_id"],
          "candidate_staged":True,"inventory_pending":True,"all_variants_zero":True,
          "order_count_unchanged":True,"active_config_changed":False},ensure_ascii=False));return 0
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,subprocess.SubprocessError):
        print(json.dumps({"error":"PROD_PRODUCT_REGISTRATION_BLOCKED","active_config_changed":False},ensure_ascii=False),file=sys.stderr)
        return 2
if __name__=="__main__":raise SystemExit(main())
