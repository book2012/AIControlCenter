from core.homepage.projection import apply_standalone_contract


def test_apply_standalone_contract_with_optional_worker():
    homepage = {
        "brain": {"state": "ONLINE", "standalone": True},
        "storage": {"exists": False, "root": "/mnt/storage"},
        "backup": {"exists": False, "root": "/mnt/storage/Backup"},
        "workers": {},
    }

    dashboard = {
        "workers": {
            "ubuntu-main": {
                "worker": {
                    "worker": "ubuntu-main",
                    "status": "OPTIONAL_UNAVAILABLE",
                    "optional": True,
                }
            }
        },
        "datacenter": {"overall_status": "UNAVAILABLE"},
    }

    result = apply_standalone_contract(homepage, dashboard)

    assert result["platform"]["status"] == "ONLINE"
    assert result["platform"]["standalone"] is True
    assert result["platform"]["ubuntu_required"] is False
    assert result["platform"]["optional_infrastructure_available"] is False

    worker = result["workers"]["ubuntu-main"]["worker"]
    assert worker["status"] == "OPTIONAL_UNAVAILABLE"
    assert worker["optional"] is True

    assert result["storage"]["required"] is False
    assert result["storage"]["scope"] == "external-worker"
    assert result["storage"]["available"] is False

    assert result["backup"]["required"] is False
    assert result["backup"]["scope"] == "external-worker"
    assert result["backup"]["available"] is False

    assert result["storage"]["root"] == "/mnt/storage"
    assert result["backup"]["root"] == "/mnt/storage/Backup"


def test_apply_standalone_contract_does_not_mutate_inputs():
    homepage = {
        "brain": {"state": "ONLINE"},
        "storage": {"exists": False},
        "backup": {"exists": False},
        "workers": {},
    }
    dashboard = {"workers": {}, "datacenter": {}}

    apply_standalone_contract(homepage, dashboard)

    assert "platform" not in homepage
    assert "required" not in homepage["storage"]
    assert "required" not in homepage["backup"]
