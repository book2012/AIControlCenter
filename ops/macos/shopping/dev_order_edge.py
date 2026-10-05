"""DEV-only edge overlay; preserve every non-DEV route/config byte semantically."""
import copy, hashlib, json
from pathlib import Path
import requests

DEV='dev.bokstory.duckdns.org'
PATHS=['/dev-order','/dev-order/*','/order-preview/*','/__order-dev/*',
       '/shopping/orders','/shopping/orders/*','/shopping/auth/session','/shopping/auth/logout']

def dev_route(config):
    found=[]
    for server in config.get('apps',{}).get('http',{}).get('servers',{}).values():
        for route in server.get('routes',[]):
            if route.get('match')==[{'host':[DEV]}]:found.append(route)
    if len(found)!=1:raise ValueError('EXACT_DEV_HOST_ROUTE_REQUIRED')
    return found[0]

def outside_dev(config):
    result=copy.deepcopy(config);target=dev_route(result)
    for server in result['apps']['http']['servers'].values():
        if target in server.get('routes',[]):server['routes'].remove(target)
    return result

def overlay(config):
    result=copy.deepcopy(config);target=dev_route(result);found=[]
    text=json.dumps(target,sort_keys=True)
    if '127.0.0.1:18445' in text:
        if not all(path in text for path in PATHS) or 'authentication' not in text:raise ValueError('UNKNOWN_DEV_OVERLAY')
        return result
    def visit(value):
        if isinstance(value,dict):
            handles=value.get('handle')
            if isinstance(handles,list):
                for index,item in enumerate(handles):
                    if item.get('handler')=='reverse_proxy' and item.get('upstreams')==[{'dial':'127.0.0.1:18080'}]:
                        if not any(v.get('handler')=='authentication' for v in handles[:index]):raise ValueError('DEV_AUTH_GUARD_REQUIRED')
                        found.append((handles,index))
            for item in value.values():visit(item)
        elif isinstance(value,list):
            for item in value:visit(item)
    visit(target)
    if len(found)!=1:raise ValueError('EXACT_DEV_UPSTREAM_REQUIRED')
    handles,index=found[0];original=copy.deepcopy(handles[index])
    handles[index]={'handler':'subroute','routes':[
        {'match':[{'path':PATHS}],'handle':[{'handler':'reverse_proxy','upstreams':[{'dial':'127.0.0.1:18445'}]}],'terminal':True},
        {'handle':[original]}]}
    if outside_dev(config)!=outside_dev(result):raise ValueError('NON_DEV_CONFIG_CHANGED')
    return result

def apply():
    before=requests.get('http://127.0.0.1:2019/config/',timeout=5).json();candidate=overlay(before)
    private=Path('/Users/kyouhan/.config/aicontrolcenter-dev-order');private.mkdir(mode=0o700,exist_ok=True)
    backup=private/'edge-before.private.json'
    if before!=candidate:
        with backup.open('x') as f:json.dump(before,f)
        backup.chmod(0o600)
        response=requests.post('http://127.0.0.1:2019/load',json=candidate,timeout=10)
        if response.status_code!=200:raise RuntimeError('DEV_EDGE_LOAD_FAILED')
    after=requests.get('http://127.0.0.1:2019/config/',timeout=5).json()
    if outside_dev(before)!=outside_dev(after):
        requests.post('http://127.0.0.1:2019/load',json=before,timeout=10)
        raise RuntimeError('EDGE_VERIFICATION_FAILED_RESTORED')
    print(json.dumps({'dev_order_paths_enabled':True,'all_non_dev_config_unchanged':True,
        'non_dev_config_sha256':hashlib.sha256(json.dumps(outside_dev(after),sort_keys=True).encode()).hexdigest()}))

if __name__=='__main__':apply()
