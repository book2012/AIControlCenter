"""Synthetic proof contracts only; no runtime collection."""
import copy
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from core.shopping.control_plane_read.runtime_components import CATEGORIES, IDENTITY_FIELDS, FIELDS, components_complete
from core.shopping.control_plane_read.effective_runtime import CHECKS, FALSE_FIELDS, reduce_evidence

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'config/deployment/shopping-runtime-component-manifest.json'


def reviewed_fixture():
    manifest = json.loads(MANIFEST.read_text())
    for category in CATEGORIES:
        manifest[category]['inventory_status'] = 'REVIEWED_COMPLETE'
        for entry in manifest[category]['required']:
            entry['version'] = entry['version'] or 'synthetic-version'
            entry['artifact_digest_or_immutable_identity'] = 'sha256:' + 'a' * 64
            entry['identity_status'] = 'REVIEWED_EXACT'
            for key in ('outbound_network_allowed', 'application_state_write_allowed', 'handles_authorization'):
                if entry[key] is None:
                    entry[key] = False
    return manifest, {c: [{k: e[k] for k in IDENTITY_FIELDS} for e in manifest[c]['required']] for c in CATEGORIES}


def evaluate(manifest, observed, facts=None):
    if facts is None:
        facts = {g: dict.fromkeys(keys, True) for g, keys in CHECKS.items()}
    return reduce_evidence(facts, manifest=manifest, observed_components=observed)


def test_repository_manifest_schema_and_unresolved_identity():
    manifest = json.loads(MANIFEST.read_text())
    schema = json.loads((ROOT / 'config/schemas/shopping-runtime-component-manifest.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(manifest)
    assert not components_complete(manifest, {c: [] for c in CATEGORIES})
    assert all(manifest[c]['inventory_status'] == 'DISCOVERY_REQUIRED' for c in CATEGORIES)
    assert all(e['artifact_digest_or_immutable_identity'] is None for e in manifest['wordpress_plugins']['required'])


@pytest.mark.parametrize('category', CATEGORIES)
def test_discovery_even_empty_blocks(category):
    manifest, observed = reviewed_fixture()
    manifest[category]['inventory_status'] = 'DISCOVERY_REQUIRED'
    assert not evaluate(manifest, observed)['deployment_logging_safety_proven']


@pytest.mark.parametrize('identifier', ['woocommerce', 'ai-shopping-storefront', 'ai-controlcenter-shopping-read'])
def test_missing_required_blocks(identifier):
    manifest, observed = reviewed_fixture()
    observed['wordpress_plugins'] = [e for e in observed['wordpress_plugins'] if e['identifier'] != identifier]
    assert not evaluate(manifest, observed)['controlled_nonprod_soft_launch_ready']
    manifest['wordpress_plugins']['required'] = [e for e in manifest['wordpress_plugins']['required'] if e['identifier'] != identifier]
    assert not components_complete(manifest, observed)


@pytest.mark.parametrize('category', CATEGORIES)
def test_unknown_component_blocks(category):
    manifest, observed = reviewed_fixture()
    unexpected = copy.deepcopy(observed['wordpress_plugins'][0])
    unexpected['identifier'] = 'unexpected'
    observed[category].append(unexpected)
    assert not components_complete(manifest, observed)


@pytest.mark.parametrize('key', CHECKS['deployment_identity'])
@pytest.mark.parametrize('value', [False, None, 'UNPROVEN', 'STALE', 'MISMATCH', 1])
def test_binding_unavailable_or_mismatched_blocks(key, value):
    manifest, observed = reviewed_fixture()
    facts = {g: dict.fromkeys(keys, True) for g, keys in CHECKS.items()}
    facts['deployment_identity'][key] = value
    result = evaluate(manifest, observed, facts)
    assert not result['deployment_logging_safety_proven']
    assert not result['controlled_nonprod_soft_launch_ready']


def test_file_policy_alone_and_edge_separation():
    manifest, observed = reviewed_fixture()
    facts = {g: dict.fromkeys(keys, True) for g, keys in CHECKS.items()}
    facts['deployment_identity'] = {}
    result = evaluate(manifest, observed, facts)
    assert result['public_edge_runtime_isolation_proven']
    assert not result['deployment_logging_safety_proven']
    facts['caddy_effective'] = {}
    assert not evaluate(manifest, observed, facts)['public_edge_runtime_isolation_proven']


def test_complete_synthetic_has_no_authority_or_side_effects():
    manifest, observed = reviewed_fixture()
    result = evaluate(manifest, observed)
    assert result['controlled_nonprod_soft_launch_ready']
    assert all(result[k] is False for k in FALSE_FIELDS)
    assert result['activation_status'] == 'BLOCKED'
    assert manifest['apache_modules']['required'] == []  # no mandated native sensor
    assert all(not e['participates_in_observation'] for e in manifest['wordpress_plugins']['required'])


@pytest.mark.parametrize('mutation', ['observation', 'wildcard', 'unknown', 'type', 'mismatch', 'duplicate'])
def test_closed_component_records(mutation):
    manifest, observed = reviewed_fixture()
    entry = manifest['wordpress_plugins']['required'][1]
    if mutation == 'observation': entry['participates_in_observation'] = True
    if mutation == 'wildcard': entry['artifact_digest_or_immutable_identity'] = '*'
    if mutation == 'unknown': entry['extra'] = True
    if mutation == 'type': entry['handles_authorization'] = 1
    if mutation == 'mismatch': entry['version'] = 'other'
    if mutation == 'duplicate': manifest['wordpress_plugins']['required'].append(copy.deepcopy(entry))
    assert not components_complete(manifest, observed)


def test_identity_shape_and_manifest_policy_owner():
    manifest, observed = reviewed_fixture()
    before = copy.deepcopy(observed)
    assert all(set(e) == IDENTITY_FIELDS for entries in observed.values() for e in entries)
    assert components_complete(manifest, observed)
    manifest['wordpress_plugins']['required'][0].update(
        role='reviewed-role', effect_class='reviewed-effects', outbound_network_allowed=True,
        application_state_write_allowed=True, handles_authorization=True)
    assert components_complete(manifest, observed)
    assert observed == before
    plugins = {e['identifier']: e for e in json.loads(MANIFEST.read_text())['wordpress_plugins']['required']}
    assert plugins['ai-shopping-storefront']['participates_in_observation'] is False
    assert plugins['ai-controlcenter-shopping-read']['participates_in_observation'] is False
    assert plugins['ai-controlcenter-shopping-read']['handles_authorization'] is True


@pytest.mark.parametrize('key', sorted(FIELDS - IDENTITY_FIELDS) + ['extra', 'category'])
def test_runtime_policy_and_unknown_fields_rejected(key):
    manifest, observed = reviewed_fixture()
    observed['wordpress_plugins'][0][key] = manifest['wordpress_plugins']['required'][0].get(key, True)
    assert not components_complete(manifest, observed)
    assert not evaluate(manifest, observed)['deployment_logging_safety_proven']


@pytest.mark.parametrize('key', ['version', 'artifact_digest_or_immutable_identity'])
@pytest.mark.parametrize('value', ['different', None, '*', '', 1])
def test_observed_identity_mismatch_blocks(key, value):
    manifest, observed = reviewed_fixture()
    observed['wordpress_plugins'][0][key] = value
    assert not components_complete(manifest, observed)


def test_duplicate_observed_identifier_blocks():
    manifest, observed = reviewed_fixture()
    observed['wordpress_plugins'].append(copy.deepcopy(observed['wordpress_plugins'][0]))
    assert not components_complete(manifest, observed)


@pytest.mark.parametrize('key,value', [('identity_status', 'UNRESOLVED'), ('version', None),
                                      ('artifact_digest_or_immutable_identity', None)])
@pytest.mark.parametrize('optional', [False, True])
def test_runtime_cannot_resolve_manifest(key, value, optional):
    manifest, observed = reviewed_fixture()
    entry = manifest['wordpress_plugins']['required'][0]
    if optional:
        entry = copy.deepcopy(entry)
        entry['identifier'] = 'optional'
        manifest['wordpress_plugins']['optional_approved'].append(entry)
    entry[key] = value
    assert not components_complete(manifest, observed)


@pytest.mark.parametrize('mismatch', [None, 'version', 'artifact_digest_or_immutable_identity'])
def test_optional_absent_or_exact_only(mismatch):
    manifest, observed = reviewed_fixture()
    entry = copy.deepcopy(manifest['wordpress_plugins']['required'][0])
    entry['identifier'] = 'optional'
    manifest['wordpress_plugins']['optional_approved'].append(entry)
    assert components_complete(manifest, observed)
    identity = {k: entry[k] for k in IDENTITY_FIELDS}
    observed['wordpress_plugins'].append(identity)
    if mismatch:
        identity[mismatch] = 'different'
    assert components_complete(manifest, observed) is (mismatch is None)
