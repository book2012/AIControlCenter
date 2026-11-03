"""Read a data-only module selection without importing or starting domains."""
import argparse
import json
from core.modules.composition import DESCRIPTORS, load_selection, resolve_selection


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    args = parser.parse_args()
    selected = resolve_selection(load_selection(args.manifest))
    print(json.dumps({"schema_version": 1, "mode": "PLAN_ONLY", "restart_required": True,
        "attached_requested": list(selected),
        "detached_requested": [x.module_id for x in DESCRIPTORS if x.module_id not in selected],
        "data_deletion": False, "production_activation": False}, sort_keys=True))


if __name__ == "__main__":
    main()
