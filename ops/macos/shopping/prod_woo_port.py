"""Explicit Mac-owned production Woo port. No activation or credential defaults."""
import base64,hashlib,json,re,subprocess
from urllib.parse import urlsplit,parse_qs
from decimal import Decimal
from datetime import timedelta,datetime
import requests
from pydantic import SecretStr
from core.shopping.models import ProductVariant
from core.shopping.order_core.guest_chat import GuestCart
from core.shopping.order_core.woocommerce_writer import WooCommerceOrderWriter,ProviderOrderWritePermit

DOCKER='/opt/homebrew/bin/docker'
def assert_production():
    d=json.loads(subprocess.check_output([DOCKER,'--context','colima-aicontrolcenter-commerce','inspect','shopping-wordpress','shopping-db'],text=True))
    for v in d:
        if v['Config']['Labels'].get('com.docker.compose.project')!='ai-shopping' or not v['State']['Running']:
            raise ValueError('PRODUCTION_PROVIDER_IDENTITY_DENIED')
        if any('aicc-order-dev' in str(m) for m in v['Mounts']):raise ValueError('PRODUCTION_PROVIDER_VOLUME_DENIED')
def php(code,payload):
    assert_production()
    encoded=base64.b64encode(json.dumps(payload,ensure_ascii=False).encode()).decode()
    script="<?php if(getenv('WORDPRESS_DB_NAME')!=='aicc_shopping'){exit(2);} require '/var/www/html/wp-load.php';add_filter('pre_wp_mail',fn()=>false);$cfg=json_decode(base64_decode('"+encoded+"'),true);"+code
    p=subprocess.run([DOCKER,'--context','colima-aicontrolcenter-commerce','exec','-i','shopping-wordpress','php'],input=script,capture_output=True,text=True,timeout=35)
    if p.returncode:raise RuntimeError('PRODUCTION_PROVIDER_UNAVAILABLE')
    if len(p.stdout)>1048576:raise ValueError('PROVIDER_RESPONSE_BOUNDS')
    return json.loads(p.stdout)
REST="""
if(!in_array($cfg['method'],['GET','POST'],true)||!preg_match('~^/wc/v3/(?:products/[1-9][0-9]*(?:/variations)?|orders(?:/[1-9][0-9]*)?)$~',$cfg['path'])){exit(3);}
if($cfg['method']==='POST'&&$cfg['path']!=='/wc/v3/orders'){exit(4);}
$users=get_users(['role'=>'administrator','number'=>1]);if(count($users)!==1){exit(5);}wp_set_current_user($users[0]->ID);
$req=new WP_REST_Request($cfg['method'],$cfg['path']);$req->set_query_params($cfg['query']);$req->set_body_params($cfg['body']);
$res=rest_do_request($req);echo wp_json_encode(['status'=>$res->get_status(),'body'=>$res->get_data()]);
"""
def rest(method,path,body=None):
    parsed=urlsplit(path)
    query={k:v[-1] for k,v in parse_qs(parsed.query).items()}
    return php(REST,{'method':method,'path':'/wc/v3/'+parsed.path,'query':query,'body':body or {}})

class ProductionCatalog:
    def __init__(self,bindings):self.products={str(v['product_id']):v for v in bindings}
    def read(self,path):
        v=rest('GET',path)
        if v['status']!=200:raise ValueError('PRODUCTION_CATALOG_UNAVAILABLE')
        return v['body']
    def get_product(self,pid):
        b=self.products[pid];raw=self.read('products/'+pid)
        if raw['id']!=b['product_id'] or raw['sku']!=b['sku'] or raw['status']!='publish':raise ValueError('PRODUCTION_PRODUCT_BINDING')
        vs=self.read('products/'+pid+'/variations?per_page=100')
        variants=tuple(ProductVariant(str(v['id']),' / '.join(str(a['option']) for a in v['attributes']),b.get('option_type','size'),v['stock_status']=='instock' and v.get('manage_stock') is True and isinstance(v.get('stock_quantity'),int) and v['stock_quantity']>0) for v in vs if v['status']=='publish')
        price=raw['price'] or str(vs[0]['price'])
        return {'id':pid,'name':raw['name'],'slug':raw['slug'],'description':raw['description'],'price':price,'currency':'KRW','category':b['category'],'in_stock':any(v.available for v in variants),'source':'woocommerce','variants':variants}

def production_quote(catalog,cart):
    cart=GuestCart.model_validate(cart);items=[];total=Decimal('0');seen=set()
    for line in cart.line_items:
        if (line.product_id,line.variation_id) in seen:raise ValueError('DUPLICATE_LINE')
        seen.add((line.product_id,line.variation_id));p=catalog.get_product(line.product_id)
        matches=[v for v in catalog.read('products/'+line.product_id+'/variations?per_page=100') if str(v['id'])==line.variation_id]
        if len(matches)!=1:raise ValueError('VARIATION_DENIED')
        v=matches[0]
        if v['status']!='publish' or v['stock_status']!='instock' or v['manage_stock'] is not True or type(v['stock_quantity']) is not int or v['stock_quantity']<line.quantity or v.get('backorders') not in ('no',None):raise ValueError('STOCK_DENIED')
        price=Decimal(v['price'])
        if not price.is_finite() or price<=0:raise ValueError('PRICE_DENIED')
        subtotal=price*line.quantity;total+=subtotal
        items.append({'product_id':line.product_id,'variation_id':line.variation_id,'quantity':line.quantity,'name':p['name'],'option':next(v.label for v in p['variants'] if v.id==line.variation_id),'unit_price':str(price),'subtotal':str(subtotal)})
    return {'line_items':items,'items_total':str(total),'shipping_fee':'0','total_tax':'0','final_total':str(total),'currency':'KRW','shipping_policy':'PROD_INCLUDED_SHIPPING'}

def provider_customer(customer):
    username='aicc-prod-'+hashlib.sha256(customer.encode()).hexdigest()[:32]
    v=php("$u=get_user_by('login',$cfg['username']);if(!$u){$id=wp_create_user($cfg['username'],wp_generate_password(48,true,true),$cfg['username'].'@example.invalid');if(is_wp_error($id)){exit(3);}$u=get_user_by('id',$id);$u->set_role('customer');update_user_meta($id,'_aicc_core_customer',$cfg['customer']);}if(!in_array('customer',$u->roles,true)||get_user_meta($u->ID,'_aicc_core_customer',true)!==$cfg['customer']){exit(4);}echo json_encode(['id'=>$u->ID]);",{'username':username,'customer':customer})
    return v['id']

class ProductionOrderSession:
    def __init__(self,*,checkout,credentials):self.checkout=checkout;self.credentials=credentials
    def endpoint(self,url):
        v=urlsplit(url)
        if v.scheme!='https' or v.netloc!='bokstory.duckdns.org' or v.query or v.fragment or not re.fullmatch('/wp-json/wc/v3/orders(?:/[1-9][0-9]*)?',v.path):raise ValueError('PRODUCTION_ORDER_ENDPOINT_DENIED')
        return v.path.removeprefix('/wp-json/wc/v3/')
    def invoke(self,method,url,**kwargs):
        if kwargs.get('auth')!=self.credentials:raise ValueError('PRODUCTION_PORT_CREDENTIAL_DENIED')
        path=self.endpoint(url);payload=kwargs.get('json');draft=None
        if method=='POST':
            tags=[m['value'] for m in payload['meta_data'] if m['key']=='_aicc_order_operation']
            if len(tags)!=1:raise ValueError('ORDER_TAG_INVALID')
            draft=self.checkout.by_provider_tag(tags[0]);body=draft['body']
            if draft['state']!='CONFIRMED':raise ValueError('CONFIRMATION_REQUIRED')
            expected=[{'product_id':int(v['product_id']),'variation_id':int(v['variation_id']),'quantity':v['quantity']} for v in body['line_items']]
            if payload['line_items']!=expected:raise ValueError('ORDER_LINE_MISMATCH')
            payload={**payload,'billing':body['billing'],'shipping':body['shipping'],'shipping_lines':[{'method_id':'aicc_included','method_title':'배송비 포함','total':'0'}],'meta_data':[*payload['meta_data'],{'key':'_aicc_delivery_digest','value':draft['digest']}]}
        value=rest(method,path,payload);raw=value['body']
        if value['status'] in (200,201):
            if method=='POST' and raw.get('customer_id')!=payload['customer_id']:raise ValueError('PROVIDER_CUSTOMER_MISMATCH')
            if draft is None:
                tags=[m.get('value') for m in raw.get('meta_data',[]) if m.get('key')=='_aicc_order_operation']
                if len(tags)!=1:raise ValueError('ORDER_BINDING_REQUIRED')
                draft=self.checkout.by_provider_tag(tags[0],allow_expired=True)
            body=draft['body']
            if draft['state']!='CONFIRMED' or any(raw[field].get(k)!=v for field in ('billing','shipping') for k,v in body[field].items()):raise ValueError('DELIVERY_MISMATCH')
            if raw['currency']!='KRW' or Decimal(raw['total'])!=Decimal(body['quote']['final_total']) or Decimal(raw['shipping_total'])!=0 or Decimal(raw['total_tax'])!=0:raise ValueError('FINAL_AMOUNT_MISMATCH')
            if [m.get('value') for m in raw['meta_data'] if m.get('key')=='_aicc_delivery_digest']!=[draft['digest']]:raise ValueError('DELIVERY_DIGEST_MISMATCH')
        response=requests.Response();response.status_code=value['status'];response._content=json.dumps(raw).encode();response._content_consumed=True;response.headers['Content-Type']='application/json';response.iter_content=lambda chunk_size:iter([response._content]);return response
    def post(self,url,**kwargs):return self.invoke('POST',url,**kwargs)
    def get(self,url,**kwargs):return self.invoke('GET',url,**kwargs)

def writer_factory(credentials,clock):
    def factory(ledger,checkout,bridge):
        def authorize(command,stamp):
            op=ledger.inspect_operation(command.idempotency_key)
            if not op or op['state']!='CLAIMED' or op['customer_id']!=command.customer_id or op['command_digest']!=command.command_digest:raise ValueError('ORDER_AUTHORITY_DENIED')
            bridge.verified_phone(command.customer_id);checkout.operation(command.idempotency_key,command.customer_id,op['session_id'])
            expires=datetime.fromisoformat(op['authority_expires_at'].replace('Z','+00:00'))
            return ProviderOrderWritePermit(command.customer_id,op['session_id'],command.idempotency_key,command.command_digest,'prod-explicit-confirmation',stamp,min(expires,stamp+timedelta(seconds=30)))
        return WooCommerceOrderWriter(base_url='https://bokstory.duckdns.org',consumer_key=SecretStr(credentials[0]),consumer_secret=SecretStr(credentials[1]),ledger=ledger,clock=clock,authorize_once=authorize,resolve_customer=provider_customer,session=ProductionOrderSession(checkout=checkout,credentials=credentials))
    return factory
