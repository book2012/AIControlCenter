"""Explicit isolated DEV commerce provisioning. Never operates on PROD compose."""
from pathlib import Path
import base64, json, os, secrets, shutil, socket, subprocess, time
import requests

REPO=Path(__file__).resolve().parents[3]
PRIVATE=Path('/Users/kyouhan/.config/aicontrolcenter-dev-order')
RUNTIME=Path('/Users/kyouhan/AIControlCenterRuntime/dev-order')
DOCKER=['docker','--context','colima-aicontrolcenter-commerce']
PROTECTED=['shopping-wordpress','shopping-db','storefront-preview-6eaaaef4-wordpress-1','storefront-preview-6eaaaef4-database-1']

def private_write(path,value):
    import tempfile
    fd,temp=tempfile.mkstemp(prefix='.dev-order-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def inspect(name):
    r=subprocess.run(DOCKER+['inspect',name],capture_output=True,text=True,check=True)
    v=json.loads(r.stdout)[0]
    return {k:(sorted(v[k],key=lambda m:m['Destination']) if k=='Mounts' else v[k]) for k in ['Id','Created','Image','Mounts']}

def main():
    for path in [PRIVATE,RUNTIME]:
        if path.is_symlink():raise RuntimeError('DEV_PATH_SYMLINK')
        path.mkdir(parents=True,exist_ok=True)
    os.chmod(PRIVATE,0o700)
    protected={name:inspect(name) for name in PROTECTED}
    secret_path=PRIVATE/'runtime.private.json'
    if secret_path.exists():cfg=json.loads(secret_path.read_text())
    else:
        with socket.socket() as probe:probe.bind(('127.0.0.1',55274))
        cfg={'environment':'DEV','admin_username':'aicc-dev-admin','admin_password':secrets.token_urlsafe(32),
             'customer_password':secrets.token_urlsafe(32),'api_password':secrets.token_urlsafe(32),
             'db_password':secrets.token_urlsafe(32),'db_root_password':secrets.token_urlsafe(32),
             'csrf_key':secrets.token_hex(32),'customer_id':'AG-CUS-'+__import__('uuid').uuid4().hex,
             'contact_ref':'AG-CON-'+__import__('uuid').uuid4().hex,'login_password':secrets.token_urlsafe(32)}
        private_write(secret_path,cfg)
    if cfg.get('environment')!='DEV':raise RuntimeError('DEV_CONFIGURATION_REQUIRED')
    source=REPO/'deploy/shopping/dev-order'
    shutil.copyfile(source/'seed.php',RUNTIME/'seed.php')
    shutil.copyfile(source/'compose.json',RUNTIME/'compose.json')
    plugins=RUNTIME/'plugins';plugins.mkdir(exist_ok=True)
    if not (plugins/'woocommerce/woocommerce.php').exists():
        subprocess.run(DOCKER+['cp','shopping-wordpress:/var/www/html/wp-content/plugins/woocommerce',str(plugins)],
                       capture_output=True,check=True)
    env=dict(os.environ,DEV_ORDER_DB_PASSWORD=cfg['db_password'],DEV_ORDER_DB_ROOT_PASSWORD=cfg['db_root_password'],
             DEV_ORDER_RUNTIME_ROOT=str(RUNTIME))
    with open(PRIVATE/'provision.log','w') as log:
        os.chmod(PRIVATE/'provision.log',0o600)
        result=subprocess.run(DOCKER+['compose','-f',str(RUNTIME/'compose.json'),'up','-d'],env=env,stdout=log,stderr=log)
        if result.returncode:raise RuntimeError('DEV_COMPOSE_START_FAILED')
    print('DEV_CONTAINERS_STARTED',flush=True)
    for _ in range(60):
        try:
            response=requests.get('http://127.0.0.1:55274/',timeout=1,allow_redirects=False)
            if response.status_code in [200,301,302,500]:break
        except requests.RequestException:pass
        time.sleep(1)
    else:raise RuntimeError('DEV_WORDPRESS_UNAVAILABLE')
    wp=json.loads(subprocess.run(DOCKER+['inspect','aicc-order-dev-wordpress-1'],capture_output=True,text=True,check=True).stdout)[0]
    if (wp['Config']['Labels'].get('com.docker.compose.project')!='aicc-order-dev'
        or any(m.get('Name','').startswith('ai-shopping-') for m in wp['Mounts'])):raise RuntimeError('DEV_ISOLATION_INVALID')
    exists=subprocess.run(DOCKER+['exec','aicc-order-dev-wordpress-1','test','-f','/var/www/html/wp-content/plugins/woocommerce/woocommerce.php']).returncode==0
    if not exists:
        subprocess.run(DOCKER+['cp',str(plugins/'woocommerce'),'aicc-order-dev-wordpress-1:/var/www/html/wp-content/plugins/'],capture_output=True,check=True)
    subprocess.run(DOCKER+['exec','aicc-order-dev-wordpress-1','chown','-R','33:33','/var/www/html/wp-content/plugins/woocommerce'],capture_output=True,check=True)
    cfg['demo_product']=requests.get('http://127.0.0.1:18080/shopping/products/oc-demo-top-0001',timeout=5).json()
    old=json.loads((PRIVATE/'commerce.private.json').read_text())
    if old.get('woocommerce',{}).get('base_url')=='https://localhost:18446':
        cfg['existing_consumer_key']=old['woocommerce'].get('consumer_key','')
        cfg['existing_consumer_secret']=old['woocommerce'].get('consumer_secret','')
    if not cfg.get('existing_consumer_key'):
        cfg['existing_consumer_key']=cfg.setdefault('bootstrap_consumer_key','ck_'+secrets.token_hex(20))
        cfg['existing_consumer_secret']=cfg.setdefault('bootstrap_consumer_secret','cs_'+secrets.token_hex(20))
    private_write(secret_path,cfg)
    def seed_call(install_only):
        payload=dict(cfg,install_only=install_only)
        code=(source/'seed.php').read_text().replace("$cfg=json_decode(file_get_contents('php://stdin'),true);",
            "$cfg=json_decode(base64_decode('"+base64.b64encode(json.dumps(payload).encode()).decode()+"'),true);")
        return subprocess.run(DOCKER+['exec','-i','aicc-order-dev-wordpress-1','php','-d','memory_limit=512M'],
                              input=code,capture_output=True,text=True,timeout=120)
    initial=seed_call(True)
    if initial.returncode:raise RuntimeError('DEV_CORE_INSTALL_FAILED')
    result=seed_call(False)
    if result.returncode:
        error=result.stderr
        for value in cfg.values():
            if isinstance(value,str) and len(value)>8:error=error.replace(value,'[REDACTED]')
        print('DEV_SEED_DIAGNOSTIC',error[-1500:],flush=True)
    try:seed=json.loads(result.stdout[result.stdout.index('{'):])
    except Exception:raise RuntimeError('DEV_SEED_FAILED') from None
    if result.returncode or not seed.get('consumer_key'):raise RuntimeError('DEV_SEED_FAILED')
    old['woocommerce']={'base_url':'https://localhost:18446','confirmed_isolated_from_prod':True,
                        'consumer_key':seed['consumer_key'],'consumer_secret':seed['consumer_secret']}
    old['test_product']['product_id']=seed['product_id']
    old['test_product']['variation_id']=next(v['id'] for v in seed['variants'] if v['label'].lower()=='s')
    old['test_customer']={'woocommerce_customer_id':seed['customer_id'],'login_username':'aicc-dev-test-customer',
                          'login_password':cfg['login_password'],'authentication_method':'explicit DEV test-account only; not phone verification'}
    cfg['provider_customer_id']=seed['customer_id'];cfg['provider_product_id']=seed['product_id'];cfg['variants']=seed['variants']
    private_write(PRIVATE/'commerce.private.json',old);private_write(secret_path,cfg)
    after={name:inspect(name) for name in PROTECTED}
    if protected!=after:raise RuntimeError('PROTECTED_RUNTIME_CHANGED')
    private_write(RUNTIME/'provision-evidence.json',{'environment':'DEV','product_id':seed['product_id'],
        'variants':seed['variants'],'provider_customer_id':seed['customer_id'],'db_volume':'aicc-order-dev-database',
        'protected_container_identity_unchanged':True,'production_mutation':False})
    print(json.dumps({'dev_provisioned':True,'product_id':seed['product_id'],'variants':seed['variants'],
                      'customer_created':True,'credentials_saved_privately':True,'protected_containers_unchanged':True},ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except Exception as error:
        code=str(error)
        print(code if __import__('re').fullmatch('[A-Z_]+',code) else 'DEV_PROVISION_FAILED_NO_SECRET_OUTPUT',flush=True)
        raise SystemExit(1)
