from pathlib import Path
import copy,json
import pytest
from ops.macos.shopping.dev_order_edge import overlay,outside_dev,PATHS
from ops.macos.shopping.dev_order_transport import PinnedDevWooOrderSession

def config(auth=True):
    handles=([{'handler':'authentication','providers':{'http_basic':{'accounts':[{'username':'dev','password':'synthetic-hash'}]}}}] if auth else [])
    handles+=[{'handler':'reverse_proxy','upstreams':[{'dial':'127.0.0.1:18080'}]}]
    return {'apps':{'http':{'servers':{'s':{'routes':[
        {'match':[{'host':['dev.bokstory.duckdns.org']}],'handle':[{'handler':'subroute','routes':[{'handle':handles}]}]},
        {'match':[{'host':['bokstory.duckdns.org']}],'handle':[{'handler':'reverse_proxy','upstreams':[{'dial':'127.0.0.1:58082'}]}]}]}}}}}

def test_edge_preserves_prod_and_requires_existing_authentication():
    original=config();snapshot=copy.deepcopy(original);candidate=overlay(original)
    assert original==snapshot and outside_dev(original)==outside_dev(candidate)
    assert '127.0.0.1:18445' in json.dumps(candidate)
    assert all(path in json.dumps(candidate) for path in PATHS)
    assert overlay(candidate)==candidate
    with pytest.raises(ValueError,match='AUTH_GUARD'):overlay(config(auth=False))

def test_edge_rejects_ambiguous_host_or_upstream():
    value=config();value['apps']['http']['servers']['s']['routes'][0]['match'][0]['host'].append('bokstory.duckdns.org')
    with pytest.raises(ValueError):overlay(value)
    value=config();value['apps']['http']['servers']['s']['routes'][0]['handle'][0]['routes'][0]['handle'][-1]['upstreams'][0]['dial']='127.0.0.1:58082'
    with pytest.raises(ValueError):overlay(value)

@pytest.mark.parametrize('url',['http://localhost/wp-json/wc/v3/orders','https://bokstory.duckdns.org/wp-json/wc/v3/orders',
    'https://localhost:443/wp-json/wc/v3/orders','https://localhost/wp-json/wc/v3/products',
    'https://localhost/wp-json/wc/v3/orders?consumer_key=x','https://localhost/wp-json/wc/v3/orders/../products'])
def test_pinned_transport_denies_every_unapproved_endpoint(url):
    with pytest.raises(ValueError):PinnedDevWooOrderSession.endpoint(url)

def test_pinned_transport_maps_only_fixed_order_paths():
    assert PinnedDevWooOrderSession.endpoint('https://localhost/wp-json/wc/v3/orders')=='https://localhost:18446/wp-json/wc/v3/orders'
    assert PinnedDevWooOrderSession.endpoint('https://localhost/wp-json/wc/v3/orders/123').endswith('/orders/123')

def test_compose_isolated_without_unshared_host_bind_or_prod_resources():
    root=Path(__file__).resolve().parents[1]
    spec=json.loads((root/'deploy/shopping/dev-order/compose.json').read_text())
    assert spec['services']['wordpress']['ports']==['127.0.0.1:55274:80']
    assert spec['services']['wordpress']['volumes']==['dev_wordpress:/var/www/html']
    assert spec['services']['database']['networks']==['internal']
    assert spec['networks']['internal']['internal'] is True
    assert all(v['name'].startswith('aicc-order-dev-') for v in spec['volumes'].values())
    extra=spec['services']['wordpress']['environment']['WORDPRESS_CONFIG_EXTRA']
    assert '$$_SERVER' in extra and 'DISABLE_WP_CRON' in extra and 'WP_HTTP_BLOCK_EXTERNAL' in extra


def test_dev_credential_handles_match_the_existing_public_receipt_contract():
    from ops.macos.shopping.dev_order_runtime import public_reference
    from core.api.schemas.customer_auth import VerificationReceiptConsumeRequest
    payload=VerificationReceiptConsumeRequest(receipt_id=public_reference("VRF"),browser_challenge=public_reference("CHL"))
    assert not payload.receipt_id.startswith("AG-")
