import json
from fastapi.testclient import TestClient
from core.homepage.preview import create_app
from core.homepage.storefront_gallery import ROOT

def test_all_uploaded_products_show_sizes_without_changing_canonical_variants():
    rows=json.loads((ROOT/'brands/agachichi/catalog/dev-upload-products.json').read_text())['products']
    with TestClient(create_app()) as client:
        for row in rows:
            text=client.get('/homepage/storefront/product/'+row['id']).text
            assert 'id="purchase-size"' in text
            if row.get('inventory_pending') is True:
                sizes=['FREE'] if row['category'] in ['bag','acc'] else ['S','M','L']
                for size in sizes:assert 'data-preview-size="'+size+'"' in text
                assert '임시 사이즈' in text and '실제 사이즈 확인 중' in text
                canonical=client.get('/shopping/products/'+row['id']).json()
                assert not canonical['in_stock']
                assert all(v['option_type']=='color' and not v['available'] for v in canonical['variants'])
                assert 'data-preview-size="' not in text.split('id="detail-variants"')[1].split('</div>')[0]
            else:
                assert 'data-preview-size="' not in text
                for size in row['inventory']:assert '>'+size+'</button>' in text
