"""Import a reviewed built-in SHOP_MEDIA_003 image locally, without network I/O.

Usage: python3 scripts/record_agachichi_media.py ID GENERATED_PNG REVIEW
Only the first PLANNED record may be imported; completed assets are preserved.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'brands/agachichi/assets/media/SHOP_MEDIA_003.json'


def record(identifier: str, source: Path, review: str):
    source = source.resolve(strict=True)
    if source.suffix != '.png' or 'generated_images' not in source.parts or not review.strip():
        raise ValueError('Expected a reviewed local built-in generated PNG')
    manifest = json.loads(MANIFEST.read_text())
    asset = next((a for a in manifest['assets'] if a['status'] == 'PLANNED'), None)
    if asset is None or asset['id'] != identifier:
        raise ValueError('Only the first actual PLANNED asset may be recorded')
    target = ROOT / asset['target_path']
    expected = ROOT / 'brands/agachichi/assets/media/catalog' / asset['category'].lower() / f'{identifier}.jpg'
    if (target != expected or not target.resolve().is_relative_to(ROOT / 'brands/agachichi/assets/media/catalog')
            or asset['product_id'] != identifier or asset['sha256'] is not None or asset['source'] is not None):
        raise ValueError('Invalid planned record or target path')
    if target.exists():
        raise ValueError('Never replace an existing asset')
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if any(a['source'].get('artifact_sha256') == source_hash for a in manifest['assets'] if a.get('source')):
        raise ValueError('Duplicate generated artifact')
    with tempfile.TemporaryDirectory(prefix='agachichi-import-') as scratch:
        jpeg = Path(scratch) / 'asset.jpg'
        subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '85',
                        str(source), '--out', str(jpeg)], check=True, capture_output=True)
        data = jpeg.read_bytes()
    if not data.startswith(b'\xff\xd8\xff') or not data.endswith(b'\xff\xd9'):
        raise ValueError('Invalid JPEG encoding')
    digest = hashlib.sha256(data).hexdigest()
    if any(a['sha256'] == digest for a in manifest['assets']):
        raise ValueError('Duplicate completed JPEG')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as output:
        output.write(data)
    asset.update(status='GENERATED', sha256=digest, source={
        'type': 'ai_generated', 'provider': 'OpenAI built-in image generator',
        'generation_artifact': str(source), 'artifact_sha256': source_hash,
        'generation_date': datetime.now(timezone.utc).date().isoformat(),
        'generation_prompt_sha256': hashlib.sha256(asset['generation_prompt'].encode()).hexdigest(),
        'review': review,
    })
    generated = sum(a['status'] == 'GENERATED' for a in manifest['assets'])
    planned = sum(a['status'] == 'PLANNED' for a in manifest['assets'])
    manifest.update(target_count=len(manifest['assets']), completed_count=generated,
                    planned_count=planned, source_distribution={
                        'ai_generated': generated, 'stock': 0, 'unverified_planned': planned})
    staging = MANIFEST.with_suffix('.json.importing')
    staging.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    staging.replace(MANIFEST)
    print(json.dumps({'id': identifier, 'generated': generated, 'planned': planned,
                      'sha256': digest, 'bytes': len(data)}))


if __name__ == '__main__':
    identifier, source_path, review = sys.argv[1:]
    record(identifier, Path(source_path), review)
