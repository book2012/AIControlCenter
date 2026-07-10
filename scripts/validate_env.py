import json
import sys

from core.runtime.env_validation import EnvironmentTemplateValidator


def main():
    result = EnvironmentTemplateValidator().validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
