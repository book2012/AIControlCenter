"""One-request, sanitized authenticated OpenAI operational smoke."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from core.providers.contracts import ProviderMessage, ProviderRequest, RetryPolicy, TimeoutPolicy
from core.providers.errors import ProviderError
from core.providers.openai_adapter import OpenAIAdapter


OPERATION = "AI-PROVIDER-01B-AUTHENTICATED-SMOKE"
MARKER = "AICONTROLCENTER_OPENAI_SMOKE_OK"


def execute(model: str, *, adapter: OpenAIAdapter | None = None) -> tuple[dict[str, object], int]:
    active_adapter = adapter or OpenAIAdapter(max_output_tokens=32)
    report: dict[str, object] = {
        "operation": OPERATION,
        "provider": "openai",
        "model": model,
        "authenticated": False,
        "request_completed": False,
        "response_id_present": False,
        "marker_observed": False,
        "network_calls": 0,
        "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        "secret_exposed": False,
        "final_status": "BLOCKED",
    }
    try:
        response = active_adapter.invoke(
            ProviderRequest(
                provider="openai",
                model=model,
                messages=(ProviderMessage(role="user", content=f"Reply with exactly this marker: {MARKER}"),),
                timeout=TimeoutPolicy(seconds=30),
                retry=RetryPolicy(max_attempts=1),
            )
        )
    except ProviderError as exc:
        report["error_code"] = exc.code.value
        return report, 1

    usage = response.usage
    report.update(
        authenticated=True,
        request_completed=True,
        response_id_present=bool(response.provider_request_id),
        marker_observed=MARKER in response.content,
        network_calls=1,
        usage={
            "input_tokens": usage.input_units if usage and usage.input_units is not None else 0,
            "output_tokens": usage.output_units if usage and usage.output_units is not None else 0,
            "total_tokens": usage.total_units if usage and usage.total_units is not None else 0,
        },
    )
    validated = bool(report["response_id_present"] and report["marker_observed"])
    report["final_status"] = "VALIDATED" if validated else "BLOCKED"
    return report, 0 if validated else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the one-request authenticated OpenAI smoke")
    parser.add_argument("--model", required=True)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    report, exit_code = execute(args.model)
    if args.as_json:
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    else:
        print(f"{OPERATION}: {report['final_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
