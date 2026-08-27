import pytest
from core.governance.control_plane.trust.canonical import CanonicalizationError, canonicalize, parse_canonical_json, parse_json_bytes

def test_canonical_round_trip(): assert parse_canonical_json(canonicalize({"z":1,"a":"é"}))=={"a":"é","z":1}
@pytest.mark.parametrize("raw",[b'{"a":1,"a":2}',b'\xef\xbb\xbf{}',b'{"a":1.5}',b'{"a":9007199254740992}',b'{"a": 1}',b'"\\ud800"',b'\xff'])
def test_strict_profile_rejects(raw):
 with pytest.raises(CanonicalizationError): parse_canonical_json(raw)
def test_raw_must_be_bytes():
 with pytest.raises(CanonicalizationError): parse_json_bytes("{}")
@pytest.mark.parametrize("value", [1.0, {"value": 1.5}])
def test_canonicalize_rejects_floats(value):
 with pytest.raises(CanonicalizationError): canonicalize(value)
@pytest.mark.parametrize("value", [9007199254740992, -9007199254740992])
def test_canonicalize_rejects_unsafe_integers(value):
 with pytest.raises(CanonicalizationError): canonicalize(value)
