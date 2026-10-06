"""Scoped DEV product commands; no product creation, deletion, or production target."""
from pathlib import Path
import base64, hashlib, json, os, re, sqlite3, subprocess, threading

CATEGORY_LABELS={"outer":"아우터","top":"상의","bottom":"하의","dress":"원피스","bag":"가방","acc":"액세서리","men":"남성","all":"전체"}
CATEGORY_ALIASES={"아우터":"outer","상의":"top","탑":"top","하의":"bottom","바텀":"bottom","원피스":"dress","드레스":"dress","가방":"bag","백":"bag","액세서리":"acc","악세사리":"acc","잡화":"acc","남성":"men","전체":"all",
                  **{key:key for key in CATEGORY_LABELS}}

HELP="""DEV 상품관리
상의 / 하의 / 아우터 / 원피스 / 가방 / 액세서리 / 남성 / 전체 리스트
예: 상의 리스트 니트 · 상품명으로 목록 안에서 검색
아우터 리스트 · 가격·세일 여부와 사이즈별 현재 재고
카멜 벨티드 롱 코트 L 재고 없음으로 변경
베이직 하이넥 니트 네이비 M 재고 3개로 변경
브라운 싱글 롱 코트 가격 200000원으로 변경
베이직 하이넥 니트 50000원으로 할인
베이직 하이넥 니트 할인 취소
브라운 싱글 롱 코트 숨김 / 다시 공개
상품명 재고 확인
가격·할인·숨김은 상품 전체, 재고는 정확한 옵션에 적용합니다.
추가는 GPT로 해주세요. 제거는 숨김으로 처리하며 영구 삭제하지 않습니다."""

class CommandDenied(ValueError):
    pass

def parse_command(text, records):
    """Exact product name, optional particles, and bounded complete grammar only."""
    clean=text.strip()
    if clean in {"상품관리","상품관리 도움말","재고관리","/products"}:
        return {"action":"help"}
    if len(clean)>300:return None
    listing=re.fullmatch(r"(.+?)\s*(?:리스트|목록)(?:\s+([^\n\r]{1,80}))?",clean)
    if listing:
        category=CATEGORY_ALIASES.get(listing[1].strip().casefold())
        if category is None:raise CommandDenied("카테고리: 상의 · 하의 · 아우터 · 원피스 · 가방 · 액세서리 · 남성 · 전체")
        return {"action":"list","category":category,"query":(listing[2] or "").strip()}
    candidates=[]
    for r in records:
        name=r["name"]
        if clean.startswith(name) and (len(clean)==len(name) or clean[len(name)] in " 은는이가"):
            rest=clean[len(name):].strip()
            rest=re.sub(r"^(?:은|는|이|가)(?:\s+|(?=[0-9]))", "", rest)
            candidates.append((r,rest))
    if len(candidates)>1:raise CommandDenied("상품명이 중복됩니다. 상품명을 구분해 주세요.")
    if not candidates:
        if re.search(r"(?:재고|가격|할인|숨김|공개|삭제|제거|상품 추가)",clean):
            raise CommandDenied("등록된 상품명을 정확히 입력해 주세요. 상품 추가는 GPT로 해주세요.")
        return None
    r,rest=candidates[0];pid=r["id"]
    if re.fullmatch(r"(?:재고|상품|가격)\s*(?:확인|조회|상태)",rest):
        return {"action":"status","id":pid}
    if re.fullmatch(r"(?:숨김|숨기기|제거|삭제)(?:으로)?(?:\s*(?:변경|해줘|처리))?",rest):
        return {"action":"hide","id":pid}
    if re.fullmatch(r"(?:다시\s*)?(?:공개|보이기|표시|복구)(?:로)?(?:\s*(?:변경|해줘|처리))?",rest):
        return {"action":"show","id":pid}
    if re.fullmatch(r"(?:할인|세일)\s*(?:취소|해제|종료)",rest):
        return {"action":"unsale","id":pid}
    m=re.fullmatch(r"가격\s*([0-9,]+)\s*원?(?:으로|로)?(?:\s*(?:변경|해줘|설정))?",rest)
    if m:
        return {"action":"price","id":pid,"amount":amount(m[1])}
    m=re.fullmatch(r"(?:가격\s*)?([0-9,]+)\s*원?(?:으로|로)?\s*(?:할인|세일)(?:\s*(?:변경|해줘|설정))?",rest)
    if m:
        return {"action":"sale","id":pid,"amount":amount(m[1])}
    m=re.fullmatch(r"(.*?)\s*재고\s*(없음|없어|품절|[0-9,]+\s*개?)(?:으로|로)?(?:\s*(?:변경|해줘|설정))?",rest)
    if m:
        option=re.sub(r"(?:은|는|이|가)$","",m[1].strip()).strip()
        tokens=option.split()
        sizes=r.get("size_options") or [str(k).upper() for k in r["inventory"]]
        colors=r.get("color_options",[])
        chosen_size=[s for s in sizes if s.upper() in [v.upper() for v in tokens]]
        chosen_color=[c for c in colors if c["label"] in tokens or c["id"] in tokens]
        allowed=set(sizes)|{s.lower() for s in sizes}|{c["label"] for c in colors}|{c["id"] for c in colors}
        if any(t not in allowed for t in tokens) or len(chosen_size)>1 or len(chosen_color)>1:
            raise CommandDenied("색상·사이즈를 정확히 입력해 주세요.")
        size=chosen_size[0] if chosen_size else sizes[0] if len(sizes)==1 else None
        color=chosen_color[0] if chosen_color else colors[0] if len(colors)==1 else None
        if size is None or (colors and color is None):
            raise CommandDenied("옵션을 구분해 주세요: "+r["name"]+" "+(" / ".join(c["label"] for c in colors)+" " if colors else "")+"/".join(sizes)+" 재고 3개")
        key=color["id"]+"--"+size.lower() if r.get("option_type")=="color_size" else (color["id"] if r.get("option_type")=="color" else size)
        qty=0 if m[2] in {"없음","없어","품절"} else amount(re.sub(r"\s*개$","",m[2]),allow_zero=True,maximum=9999)
        return {"action":"stock","id":pid,"key":key,"quantity":qty}
    raise CommandDenied("명령을 구분하지 못했습니다. ‘상품관리’로 사용 예시를 확인해 주세요.")

def amount(value,allow_zero=False,maximum=10000000):
    if not re.fullmatch(r"(?:[0-9]+|[1-9][0-9]{0,2}(?:,[0-9]{3})+)",value):
        raise CommandDenied("금액·수량을 숫자로 입력해 주세요.")
    n=int(value.replace(",",""))
    if n<(0 if allow_zero else 1) or n>maximum:raise CommandDenied("금액·수량 범위를 확인해 주세요.")
    return n

def option_label(record,key):
    if record.get("option_type")=="color_size":
        color,size=key.split("--")
        return next(c["label"] for c in record["color_options"] if c["id"]==color)+" / "+size.upper()
    if record.get("option_type")=="color":
        return next(c["label"] for c in record["color_options"] if c["id"]==key)
    return key.upper()

class DevProductOperator:
    def __init__(self,*,records,provider,path,projection_path,catalog_hash):
        self.records=records;self.provider=provider;self.path=Path(path);self.projection_path=Path(projection_path)
        self.catalog_hash=catalog_hash;self.lock=threading.RLock()
        self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS product_commands (update_id INTEGER PRIMARY KEY,digest TEXT NOT NULL,body TEXT NOT NULL,state TEXT NOT NULL,reply TEXT)")
        os.chmod(self.path,0o600)
    def publish(self,snapshot):
        from core.homepage.dev_product_projection import apply_projection
        data={"schema_version":1,"environment":"DEV","catalog_sha256":self.catalog_hash,"products":snapshot}
        apply_projection(self.records,data,self.catalog_hash)
        temp=self.projection_path.with_suffix(".tmp")
        with temp.open("w") as f:
            os.chmod(temp,0o600);json.dump(data,f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
        temp.replace(self.projection_path)
    def sync(self):
        with self.lock:self.publish(self.provider.snapshot())
    def command(self,text,update_id):
        try:cmd=parse_command(text,self.records)
        except CommandDenied as e:return str(e)
        if cmd is None:return None
        if cmd["action"]=="help":return HELP
        with self.lock:
            if cmd["action"]=="list":
                snap=self.provider.snapshot();self.publish(snap)
                records=[r for r in self.records if cmd["category"]=="all" or r["category"]==cmd["category"]]
                label=CATEGORY_LABELS[cmd["category"]];query=cmd.get("query","")
                if query:records=[r for r in records if query.casefold() in r["name"].casefold()]
                if not records:return ("[DEV] "+label+"에서 ‘"+query+"’에 맞는 상품이 없습니다." if query else "[DEV] 등록된 "+label+" 상품이 없습니다.")
                blocks=["[DEV] "+label+" 재고 · "+str(len(records))+"개 상품"+(" · 검색: "+query if query else "")]
                for r in records:
                    row=snap[r["id"]]
                    title=r["name"]+(" [숨김]" if not row["enabled"] else "")
                    sizes=["  "+option_label(r,k)+": "+("품절 (0개)" if v==0 else str(v)+"개") for k,v in row["inventory"].items()]
                    price=("SALE · 정상가 "+format(row["regular_price"],",")+"원 → 할인가 "+format(row["sale_price"],",")+"원"
                           if row["sale_price"] is not None else "가격 "+format(row["regular_price"],",")+"원 · 세일 아님")
                    blocks.append(title+"\n"+price+"\n"+"\n".join(sizes))
                return "\n\n".join(blocks)
            if cmd["action"]=="status":
                snap=self.provider.snapshot();self.publish(snap)
                row=snap[cmd["id"]];r=next(r for r in self.records if r["id"]==cmd["id"])
                return r["name"]+" · "+("공개" if row["enabled"] else "숨김")+" · "+format(row["sale_price"] or row["regular_price"],",")+"원"+(" · SALE" if row["sale_price"] else "")+"\n"+", ".join(option_label(r,k)+": "+str(v)+"개" for k,v in row["inventory"].items())
            if type(update_id) is not int or not 0<=update_id<2**63-1:raise ValueError("UPDATE_ID_REQUIRED")
            body=json.dumps(cmd,sort_keys=True,ensure_ascii=False);digest=hashlib.sha256(body.encode()).hexdigest()
            with sqlite3.connect(self.path) as c:
                old=c.execute("SELECT digest,state,reply FROM product_commands WHERE update_id=?",(update_id,)).fetchone()
                if old:
                    if old[0]!=digest:raise ValueError("COMMAND_REPLAY_CONFLICT")
                    if old[1] in {"APPLIED","REJECTED"}:return old[2]
                else:c.execute("INSERT INTO product_commands VALUES (?,?,?,'PENDING',NULL)",(update_id,digest,body))
            return self._apply(update_id,cmd,digest)
    def _apply(self,update_id,cmd,digest):
        try:
            snap=self.provider.apply(cmd,update_id,digest);self.publish(snap)
        except CommandDenied as e:
            reply=str(e);state="REJECTED"
        except Exception:
            # Durable PENDING is reconciled by the worker with the same provider receipt key.
            return "변경 결과를 확인 중입니다. 중복 변경 없이 재확인하고 있으니 재전송하지 마세요."
        else:
            r=next(r for r in self.records if r["id"]==cmd["id"])
            row=snap[cmd["id"]];action=cmd["action"]
            value=("재고 "+option_label(r,cmd["key"])+": "+str(cmd["quantity"])+"개" if action=="stock" else
                "가격 "+format(row["regular_price"],",")+"원" if action=="price" else
                "SALE "+format(row["sale_price"],",")+"원" if action=="sale" else
                "할인 해제" if action=="unsale" else "숨김 완료 · 다시 공개 가능" if action=="hide" else "다시 공개 완료")
            reply="[DEV] "+r["name"]+" · "+value;state="APPLIED"
        with sqlite3.connect(self.path) as c:
            c.execute("UPDATE product_commands SET state=?,reply=? WHERE update_id=?",(state,reply,update_id))
        return reply
    def recover(self):
        with self.lock:
            with sqlite3.connect(self.path) as c:rows=c.execute("SELECT update_id,body,digest FROM product_commands WHERE state='PENDING' ORDER BY update_id LIMIT 5").fetchall()
            replies=[]
            for i,b,d in rows:
                reply=self._apply(i,json.loads(b),d)
                with sqlite3.connect(self.path) as c:state=c.execute("SELECT state FROM product_commands WHERE update_id=?",(i,)).fetchone()[0]
                if state in {"APPLIED","REJECTED"}:replies.append(reply)
            return replies

class DevWooProductProvider:
    def __init__(self,*,records,bindings,assert_isolation):
        self.records=records;self.assert_isolation=assert_isolation
        self.rows=[]
        for r in records:
            b=[v for v in bindings if v["demo_id"]==r["id"]]
            if len(b)!=1 or b[0]["sku"]!="aicc-dev-"+r["id"]:raise ValueError("DEV_PRODUCT_SCOPE")
            colors={c["id"]:c["label"] for c in r.get("color_options",[])}
            options={}
            for key in r["inventory"]:
                if r.get("option_type")=="color_size":
                    color,size=key.split("--");options[key]={"color":colors[color],"size":size.upper()}
                elif r.get("option_type","size")=="size":options[key]={"size":key.upper()}
                else:options[key]={"color":colors[key]}
            self.rows.append({"id":r["id"],"provider_id":b[0]["product_id"],"sku":b[0]["sku"],"options":options})
    def call(self,cmd=None,update_id=None,digest=None):
        self.assert_isolation()
        payload=base64.b64encode(json.dumps({"rows":self.rows,"command":cmd,"update_id":update_id,"digest":digest},ensure_ascii=False).encode()).decode()
        p=subprocess.run(["docker","--context","colima-aicontrolcenter-commerce","exec","-i","aicc-order-dev-wordpress-1","php"],
            input=PHP.replace("__PAYLOAD__",payload),capture_output=True,text=True,timeout=35)
        if p.returncode:
            if "SALE_PRICE" in p.stderr:raise CommandDenied("할인가를 정상 가격보다 낮게 입력해 주세요.")
            raise RuntimeError("DEV_PRODUCT_PROVIDER_UNAVAILABLE")
        data=json.loads(p.stdout)
        if data.get("environment")!="DEV":raise RuntimeError("DEV_PRODUCT_RECEIPT")
        return data["products"]
    def snapshot(self):return self.call()
    def apply(self,cmd,update_id,digest):return self.call(cmd,update_id,digest)

PHP=r"""<?php
if(getenv('WORDPRESS_DB_NAME')!=='aicc_order_dev'){exit(2);}
require '/var/www/html/wp-load.php';
add_filter('pre_wp_mail',fn()=>false);
$cfg=json_decode(base64_decode('__PAYLOAD__'),true);global $wpdb;
if($wpdb->get_var("SELECT GET_LOCK('aicc_dev_stock_confirmation',5)")!=='1'){exit(3);}
try{
 $bad=$wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND engine IS NOT NULL AND engine<>'InnoDB'",DB_NAME));
 if((int)$bad!==0){throw new Exception('ENGINE');}
 $wpdb->query('START TRANSACTION');$bound=[];
 foreach($cfg['rows'] as $r){
  if(!preg_match('/^ag-upload-(top|bottom|outer|dress|bag|acc)-[0-9]{4}$/',$r['id'])){throw new Exception('SCOPE');}
  $p=wc_get_product($r['provider_id']);
  if(!$p||!$p->is_type('variable')||$p->get_sku()!==$r['sku']||$p->get_meta('_aicc_catalog_id')!==$r['id']||!in_array($p->get_status(),['publish','draft'],true)){throw new Exception('BINDING');}
  $vs=[];
  foreach($p->get_children() as $vid){
   $v=wc_get_product($vid);if($v->get_status()!=='publish'){continue;}
   $matches=[];foreach($r['options'] as $key=>$attrs){$ok=true;foreach($attrs as $a=>$value){if($v->get_attribute($a)!==$value){$ok=false;}}if($ok){$matches[]=$key;}}
   if(count($matches)!==1||isset($vs[$matches[0]])||!$v->managing_stock()||$v->get_backorders()!=='no'||!is_int($v->get_stock_quantity())||$v->get_stock_quantity()<0){throw new Exception('VARIANT');}
   $vs[$matches[0]]=$v;
  }
  if(count($vs)!==count($r['options'])){throw new Exception('OPTIONS');}
  $bound[$r['id']]=[$p,$vs];
 }
 $cmd=$cfg['command'];$receipt=null;$replay=false;
 if($cmd){
  if(!isset($bound[$cmd['id']])||!is_int($cfg['update_id'])||!preg_match('/^[0-9a-f]{64}$/',$cfg['digest'])){throw new Exception('COMMAND');}
  $receipt='aicc_dev_product_update_'.$cfg['update_id'];$saved=get_option($receipt);
  if($saved){if($saved!==$cfg['digest']){throw new Exception('REPLAY');}$replay=true;}
  if(!$replay){
   [$p,$vs]=$bound[$cmd['id']];$action=$cmd['action'];
   if($action==='stock'){
    if(!isset($vs[$cmd['key']])||!is_int($cmd['quantity'])||$cmd['quantity']<0||$cmd['quantity']>9999){throw new Exception('STOCK');}
    $v=$vs[$cmd['key']];$v->set_stock_quantity($cmd['quantity']);$v->set_stock_status($cmd['quantity']>0?'instock':'outofstock');$v->save();
   }elseif(in_array($action,['price','sale','unsale'],true)){
    if($action!=='unsale'&&(!is_int($cmd['amount'])||$cmd['amount']<1||$cmd['amount']>10000000)){throw new Exception('PRICE');}
    foreach($vs as $v){if($action==='sale'&&(int)$v->get_regular_price()<=$cmd['amount']){throw new Exception('SALE_PRICE');}}
    foreach($vs as $v){
     if($action==='price'){$v->set_regular_price((string)$cmd['amount']);$v->set_sale_price('');}
     elseif($action==='sale'){$v->set_sale_price((string)$cmd['amount']);}
     else{$v->set_sale_price('');}
     $v->set_date_on_sale_from(null);$v->set_date_on_sale_to(null);$v->set_price($v->get_sale_price()!==''?$v->get_sale_price():$v->get_regular_price());$v->save();
    }
    $tags=$p->get_tag_ids();$term=get_term_by('slug','aicc-dev-sale','product_tag');
    if($action==='sale'&&!$term){$made=wp_insert_term('SALE','product_tag',['slug'=>'aicc-dev-sale']);if(is_wp_error($made)){throw new Exception('TAG');}$term=get_term($made['term_id'],'product_tag');}
    if($term){$tags=array_values(array_diff($tags,[$term->term_id]));if($action==='sale'){$tags[]=$term->term_id;}}
    $p->set_tag_ids($tags);$p->save();
   }elseif(in_array($action,['hide','show'],true)){$p->set_status($action==='hide'?'draft':'publish');$p->save();}
   else{throw new Exception('ACTION');}
   WC_Product_Variable::sync($p->get_id());wc_delete_product_transients($p->get_id());
   if(!add_option($receipt,$cfg['digest'],'','no')){throw new Exception('RECEIPT');}
  }
 }
 $result=[];
 foreach($bound as $id=>$value){
  [$p,$vs]=$value;$p=wc_get_product($p->get_id());$inventory=[];$regular=[];$sale=[];
  foreach($vs as $key=>$v){
   $v=wc_get_product($v->get_id());$inventory[$key]=$v->get_stock_quantity();$regular[]=$v->get_regular_price();$sale[]=$v->get_sale_price();
  }
  if(count(array_unique($regular))!==1||count(array_unique($sale))!==1){throw new Exception('UNIFORM_PRICE');}
  $result[$id]=['enabled'=>$p->get_status()==='publish','regular_price'=>(int)$regular[0],'sale_price'=>$sale[0]===''?null:(int)$sale[0],'inventory'=>$inventory];
 }
 $wpdb->query($cmd?'COMMIT':'ROLLBACK');
 echo wp_json_encode(['environment'=>'DEV','products'=>$result,'replayed'=>$replay]);
}catch(Throwable $e){$wpdb->query('ROLLBACK');fwrite(STDERR,$e->getMessage());exit(4);}
finally{$wpdb->get_var("SELECT RELEASE_LOCK('aicc_dev_stock_confirmation')");}
"""
