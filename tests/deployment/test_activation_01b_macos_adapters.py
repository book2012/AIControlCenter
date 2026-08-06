from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json
import subprocess

import pytest

from core.deployment.activation_inspector import (
    LAUNCHCTL,
    LSOF,
    CommandRequest,
    CommandResult,
    HttpProbeRequest,
    HttpProbeResponse,
    MacOSObservationError,
    MacOSReadOnlyAdapter,
    StdlibHttpTransport,
    SubprocessCommandExecutor,
    parse_launchctl_print,
    parse_lsof_fields,
)


class RecordingExecutor:
    def __init__(
        self,
        results: list[CommandResult],
    ) -> None:
        self.results = list(results)
        self.requests: list[CommandRequest] = []

    def run(
        self,
        request: CommandRequest,
    ) -> CommandResult:
        self.requests.append(request)

        if not self.results:
            raise AssertionError(
                "No fake command result available"
            )

        return self.results.pop(0)


class RecordingTransport:
    def __init__(
        self,
        response: HttpProbeResponse,
    ) -> None:
        self.response = response
        self.requests: list[HttpProbeRequest] = []

    def probe(
        self,
        request: HttpProbeRequest,
    ) -> HttpProbeResponse:
        self.requests.append(request)
        return self.response


def adapter(
    *,
    results: list[CommandResult],
    response: HttpProbeResponse | None = None,
) -> tuple[
    MacOSReadOnlyAdapter,
    RecordingExecutor,
    RecordingTransport,
]:
    executor = RecordingExecutor(results)
    transport = RecordingTransport(
        response
        or HttpProbeResponse(
            status=200,
            body=b"{}",
        )
    )

    return (
        MacOSReadOnlyAdapter(
            executor=executor,
            http_transport=transport,
        ),
        executor,
        transport,
    )


def test_command_request_is_fail_closed() -> None:
    with pytest.raises(ValueError):
        CommandRequest(
            argv=("launchctl", "print", "x")
        )

    with pytest.raises(ValueError):
        CommandRequest(
            argv=("/bin/echo", "ok"),
            env={"PYTHONPATH": "/tmp"},
        )

    with pytest.raises(ValueError):
        CommandRequest(
            argv=("/bin/echo", "bad\nvalue"),
        )


def test_subprocess_executor_uses_closed_environment() -> None:
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs

        return SimpleNamespace(
            returncode=0,
            stdout=b"ok",
            stderr=b"",
        )

    executor = SubprocessCommandExecutor(
        run_callable=fake_run
    )

    result = executor.run(
        CommandRequest(
            argv=("/bin/echo", "ok"),
            env={"CUSTOM": "value"},
        )
    )

    assert result.returncode == 0
    assert captured["argv"] == [
        "/bin/echo",
        "ok",
    ]

    kwargs = captured["kwargs"]

    assert kwargs["shell"] is False
    assert kwargs["check"] is False
    assert kwargs["text"] is False
    assert kwargs["stdin"] is subprocess.DEVNULL
    assert "HOME" not in kwargs["env"]
    assert "PYTHONPATH" not in kwargs["env"]
    assert kwargs["env"]["CUSTOM"] == "value"
    assert kwargs["env"]["PYTHONNOUSERSITE"] == "1"
    assert kwargs["env"]["PYTHONDONTWRITEBYTECODE"] == "1"


def test_launchctl_print_is_exact_and_parsed() -> None:
    subject, executor, _ = adapter(
        results=[
            CommandResult(
                returncode=0,
                stdout=(
                    b"system/com.aicontrolcenter.api.shadow = {\n"
                    b"\tstate = running\n"
                    b"\tpid = 4242\n"
                    b"\tusername = kyouhan\n"
                    b"}\n"
                ),
                stderr=b"",
            )
        ]
    )

    result = subject.inspect_launchd(
        "system/com.aicontrolcenter.api.shadow"
    )

    request = executor.requests[0]

    assert request.argv == (
        LAUNCHCTL,
        "print",
        "system/com.aicontrolcenter.api.shadow",
    )

    assert result.running is True
    assert result.pid == 4242
    assert result.application_user == "kyouhan"
    assert result.to_payload()["allowed_operation"] == "print"


def test_launchctl_conflicting_fields_fail_closed() -> None:
    with pytest.raises(
        MacOSObservationError,
        match="LAUNCHD_CONFLICTING_FIELD",
    ):
        parse_launchctl_print(
            identity="system/example",
            stdout=(
                b"state = running\n"
                b"state = waiting\n"
            ),
        )


def test_lsof_command_is_exact_and_parsed() -> None:
    subject, executor, _ = adapter(
        results=[
            CommandResult(
                returncode=0,
                stdout=(
                    b"p4242\n"
                    b"cpython\n"
                    b"Lkyouhan\n"
                    b"PTCP\n"
                    b"n127.0.0.1:18100\n"
                    b"TST=LISTEN\n"
                ),
                stderr=b"",
            )
        ]
    )

    records = subject.inspect_listeners(
        host="127.0.0.1",
        port=18100,
    )

    request = executor.requests[0]

    assert request.argv == (
        LSOF,
        "-nP",
        "-a",
        "-iTCP@127.0.0.1:18100",
        "-sTCP:LISTEN",
        "-FpcLnPT",
    )

    assert len(records) == 1
    assert records[0].pid == 4242
    assert records[0].name == "127.0.0.1:18100"
    assert records[0].state == "LISTEN"


def test_lsof_no_listener_is_empty_observation() -> None:
    subject, _, _ = adapter(
        results=[
            CommandResult(
                returncode=1,
                stdout=b"",
                stderr=b"",
            )
        ]
    )

    assert (
        subject.inspect_listeners(
            host="127.0.0.1",
            port=18100,
        )
        == ()
    )


def test_lsof_malformed_stream_fails_closed() -> None:
    with pytest.raises(
        MacOSObservationError,
        match="LSOF_FIELD_WITHOUT_PROCESS",
    ):
        parse_lsof_fields(
            b"cpython\n"
        )


def test_runtime_filesystem_is_read_only_and_bounded(
    tmp_path: Path,
) -> None:
    runtime = tmp_path / "runtime"
    release = runtime / "releases" / "candidate123"
    release.mkdir(parents=True)

    current_release = (
        runtime
        / "releases"
        / "active123"
    )

    current_release.mkdir()

    (runtime / "current").symlink_to(
        Path("releases") / "active123"
    )

    metadata = {
        "runtime_id": "candidate123",
        "source_commit": "b" * 40,
    }

    (
        release
        / "runtime-metadata.json"
    ).write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    (
        release
        / ".aicontrolcenter-source-commit"
    ).write_text(
        "b" * 40 + "\n",
        encoding="utf-8",
    )

    python_path = release / "bin" / "python"
    python_path.parent.mkdir()
    python_path.write_bytes(b"fixture-python")

    subject, _, _ = adapter(results=[])

    result = subject.inspect_runtime_filesystem(
        runtime_root=str(runtime),
        current_link_name="current",
        candidate_runtime="candidate123",
        metadata_filename="runtime-metadata.json",
        source_marker_filename=(
            ".aicontrolcenter-source-commit"
        ),
        python_relative_path="bin/python",
    )

    assert result.current_runtime == "active123"
    assert result.candidate_runtime == "candidate123"
    assert result.metadata == metadata
    assert result.source_marker_commit == "b" * 40
    assert result.python_executable == str(python_path)


def test_runtime_current_escape_is_rejected(
    tmp_path: Path,
) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()

    outside = tmp_path / "outside"
    outside.mkdir()

    (runtime / "current").symlink_to(
        outside
    )

    subject, _, _ = adapter(results=[])

    with pytest.raises(
        MacOSObservationError,
        match="RUNTIME_CURRENT_ESCAPED_ROOT",
    ):
        subject.inspect_runtime_filesystem(
            runtime_root=str(runtime),
            current_link_name="current",
            candidate_runtime="candidate123",
            metadata_filename="runtime-metadata.json",
            source_marker_filename=(
                ".aicontrolcenter-source-commit"
            ),
            python_relative_path="bin/python",
        )


def test_runtime_python_probe_is_exact() -> None:
    executable = (
        "/Users/example/Library/Application Support/"
        "AIControlCenter/runtime/releases/"
        "candidate123/bin/python"
    )

    subject, executor, _ = adapter(
        results=[
            CommandResult(
                returncode=0,
                stdout=b"Python 3.14.6\n",
                stderr=b"",
            )
        ]
    )

    result = subject.probe_runtime_python(
        executable
    )

    request = executor.requests[0]

    assert request.argv == (
        executable,
        "-I",
        "-S",
        "--version",
    )

    assert request.env == {}
    assert result.version == "Python 3.14.6"


def test_http_contract_rejects_unsafe_requests() -> None:
    with pytest.raises(ValueError):
        HttpProbeRequest(
            probe_id="external",
            host="example.com",
            port=443,
            method="GET",
            path="/health",
            expected_status=200,
        )

    with pytest.raises(ValueError):
        HttpProbeRequest(
            probe_id="unsafe-post",
            host="127.0.0.1",
            port=18100,
            method="POST",
            path="/shopping/products",
            expected_status=405,
        )

    with pytest.raises(ValueError):
        HttpProbeRequest(
            probe_id="retry",
            host="127.0.0.1",
            port=18100,
            method="GET",
            path="/health",
            expected_status=200,
            attempt_count=2,
        )


def test_stdlib_http_transport_is_single_attempt() -> None:
    calls = []

    class FakeResponse:
        status = 405

        def read(self, amount):
            calls.append(
                ("read", amount)
            )
            return b""

    class FakeConnection:
        def __init__(
            self,
            host,
            port,
            timeout,
        ):
            calls.append(
                (
                    "connect",
                    host,
                    port,
                    timeout,
                )
            )

        def request(
            self,
            method,
            path,
            body,
            headers,
        ):
            calls.append(
                (
                    "request",
                    method,
                    path,
                    body,
                    headers,
                )
            )

        def getresponse(self):
            calls.append(("response",))
            return FakeResponse()

        def close(self):
            calls.append(("close",))

    transport = StdlibHttpTransport(
        connection_factory=FakeConnection
    )

    request = HttpProbeRequest(
        probe_id="post-health-denied",
        host="127.0.0.1",
        port=18100,
        method="POST",
        path="/health",
        expected_status=405,
    )

    response = transport.probe(request)

    assert response.status == 405
    assert response.body == b""

    request_calls = [
        call
        for call in calls
        if call[0] == "request"
    ]

    assert len(request_calls) == 1
    assert request_calls[0][3] == b""
    assert calls[-1] == ("close",)


def test_adapter_http_delegates_once() -> None:
    subject, _, transport = adapter(
        results=[],
        response=HttpProbeResponse(
            status=200,
            body=b'{"status":"ok"}',
        ),
    )

    request = HttpProbeRequest(
        probe_id="get-health",
        host="127.0.0.1",
        port=18100,
        method="GET",
        path="/health",
        expected_status=200,
    )

    response = subject.probe_http(request)

    assert response.status == 200
    assert transport.requests == [request]


def test_adapter_commands_are_read_only_only() -> None:
    subject, executor, _ = adapter(
        results=[
            CommandResult(
                returncode=0,
                stdout=(
                    b"state = running\n"
                    b"pid = 4242\n"
                ),
                stderr=b"",
            ),
            CommandResult(
                returncode=1,
                stdout=b"",
                stderr=b"",
            ),
            CommandResult(
                returncode=0,
                stdout=b"Python 3.14.6\n",
                stderr=b"",
            ),
        ]
    )

    subject.inspect_launchd(
        "system/com.aicontrolcenter.api.shadow"
    )

    subject.inspect_listeners(
        host="127.0.0.1",
        port=18100,
    )

    subject.probe_runtime_python(
        "/Users/example/runtime/bin/python"
    )

    forbidden = {
        "bootstrap",
        "bootout",
        "disable",
        "enable",
        "kickstart",
        "kill",
        "load",
        "remove",
        "start",
        "stop",
        "unload",
        "write",
    }

    for request in executor.requests:
        lowered = {
            argument.lower()
            for argument in request.argv
        }

        assert lowered.isdisjoint(forbidden)

    assert executor.requests[0].argv[1] == "print"
