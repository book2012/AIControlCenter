from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping
import http.client
import json
import os
import re
import subprocess

from .ports import (
    CommandExecutor,
    CommandRequest,
    CommandResult,
    HttpProbeRequest,
    HttpProbeResponse,
    HttpTransport,
)


LAUNCHCTL = "/bin/launchctl"
LSOF = "/usr/sbin/lsof"

_SAFE_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "LANG": "C",
    "LC_ALL": "C",
    "PYTHONNOUSERSITE": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
}

_LAUNCHD_IDENTITY = re.compile(
    r"^system/[A-Za-z0-9][A-Za-z0-9._-]{1,199}$"
)

_RUNTIME_ID = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$"
)

_COMMIT_ID = re.compile(
    r"^[0-9a-f]{40}$"
)

_PYTHON_VERSION = re.compile(
    r"^Python [0-9]+\.[0-9]+\.[0-9]+"
)


class MacOSObservationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LaunchdObservation:
    identity: str
    available: bool
    running: bool
    pid: int | None
    application_user: str | None
    state: str
    program_arguments: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "available": self.available,
            "running": self.running,
            "pid": self.pid,
            "application_user": (
                self.application_user
            ),
            "allowed_operation": "print",
        }


@dataclass(frozen=True, slots=True)
class ListenerRecord:
    pid: int
    command: str | None
    login: str | None
    protocol: str | None
    name: str
    state: str | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "pid": self.pid,
            "command": self.command,
            "login": self.login,
            "protocol": self.protocol,
            "name": self.name,
            "state": self.state,
        }


@dataclass(frozen=True, slots=True)
class RuntimeFilesystemObservation:
    current_runtime: str
    candidate_runtime: str
    candidate_available: bool
    metadata: Mapping[str, Any]
    source_marker_commit: str
    python_executable: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "current_runtime": self.current_runtime,
            "candidate_runtime": self.candidate_runtime,
            "candidate_available": (
                self.candidate_available
            ),
            "metadata": dict(self.metadata),
            "source_marker_commit": (
                self.source_marker_commit
            ),
            "python_executable": (
                self.python_executable
            ),
        }


@dataclass(frozen=True, slots=True)
class RuntimePythonObservation:
    executable: str
    version: str
    returncode: int

    def to_payload(self) -> dict[str, Any]:
        return {
            "executable": self.executable,
            "version": self.version,
            "returncode": self.returncode,
        }


def _as_bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""

    if isinstance(value, bytes):
        return value

    return value.encode("utf-8", errors="strict")


def _bounded_utf8(
    value: bytes,
    *,
    limit: int,
    component: str,
) -> str:
    if len(value) > limit:
        raise MacOSObservationError(
            component + "_OUTPUT_LIMIT_EXCEEDED"
        )

    try:
        return value.decode(
            "utf-8",
            errors="strict",
        )
    except UnicodeDecodeError as error:
        raise MacOSObservationError(
            component + "_INVALID_UTF8"
        ) from error


def _bounded_read(
    path: Path,
    *,
    limit: int,
    component: str,
) -> bytes:
    if path.is_symlink():
        raise MacOSObservationError(
            component + "_SYMLINK_REJECTED"
        )

    try:
        with path.open("rb") as handle:
            value = handle.read(limit + 1)
    except OSError as error:
        raise MacOSObservationError(
            component + "_READ_FAILED"
        ) from error

    if len(value) > limit:
        raise MacOSObservationError(
            component + "_SIZE_LIMIT_EXCEEDED"
        )

    return value


def _safe_relative_path(
    value: str,
) -> PurePosixPath:
    path = PurePosixPath(value)

    if (
        path.is_absolute()
        or not path.parts
        or any(
            part in {"", ".", ".."}
            for part in path.parts
        )
    ):
        raise MacOSObservationError(
            "RUNTIME_RELATIVE_PATH_INVALID"
        )

    return path


class SubprocessCommandExecutor:
    def __init__(
        self,
        run_callable: Callable[..., Any] | None = None,
    ) -> None:
        self._run = (
            subprocess.run
            if run_callable is None
            else run_callable
        )

    def run(
        self,
        request: CommandRequest,
    ) -> CommandResult:
        environment = dict(_SAFE_ENVIRONMENT)
        environment.update(dict(request.env or {}))
        environment.pop("PYTHONPATH", None)

        try:
            completed = self._run(
                list(request.argv),
                cwd=request.cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=request.timeout_seconds,
                check=False,
                shell=False,
                text=False,
            )
        except subprocess.TimeoutExpired as error:
            stdout = _as_bytes(error.stdout)
            stderr = _as_bytes(error.stderr)

            if (
                len(stdout) + len(stderr)
                > request.max_output_bytes
            ):
                raise MacOSObservationError(
                    "COMMAND_OUTPUT_LIMIT_EXCEEDED"
                ) from error

            return CommandResult(
                returncode=124,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
            )
        except OSError as error:
            raise MacOSObservationError(
                "COMMAND_EXECUTION_FAILED"
            ) from error

        stdout = _as_bytes(completed.stdout)
        stderr = _as_bytes(completed.stderr)

        if (
            len(stdout) + len(stderr)
            > request.max_output_bytes
        ):
            raise MacOSObservationError(
                "COMMAND_OUTPUT_LIMIT_EXCEEDED"
            )

        return CommandResult(
            returncode=int(completed.returncode),
            stdout=stdout,
            stderr=stderr,
            timed_out=False,
        )


class StdlibHttpTransport:
    def __init__(
        self,
        connection_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._connection_factory = (
            http.client.HTTPConnection
            if connection_factory is None
            else connection_factory
        )

    def probe(
        self,
        request: HttpProbeRequest,
    ) -> HttpProbeResponse:
        connection = self._connection_factory(
            request.host,
            request.port,
            timeout=request.timeout_seconds,
        )

        try:
            connection.request(
                request.method,
                request.path,
                body=request.body,
                headers={
                    "Connection": "close",
                    "Content-Length": "0",
                },
            )

            response = connection.getresponse()
            body = response.read(
                request.max_body_bytes + 1
            )

            if len(body) > request.max_body_bytes:
                raise MacOSObservationError(
                    "HTTP_BODY_LIMIT_EXCEEDED"
                )

            return HttpProbeResponse(
                status=int(response.status),
                body=bytes(body),
            )
        except MacOSObservationError:
            raise
        except Exception as error:
            raise MacOSObservationError(
                "HTTP_PROBE_FAILED"
            ) from error
        finally:
            connection.close()


def parse_launchctl_print(
    *,
    identity: str,
    stdout: bytes,
    max_output_bytes: int = 262_144,
) -> LaunchdObservation:
    text = _bounded_utf8(
        stdout,
        limit=max_output_bytes,
        component="LAUNCHD",
    )

    lines = text.splitlines()

    if len(lines) > 4096:
        raise MacOSObservationError(
            "LAUNCHD_LINE_LIMIT_EXCEEDED"
        )

    first_nonempty = next(
        (
            line.strip()
            for line in lines
            if line.strip()
        ),
        "",
    )

    service_depth = (
        1
        if first_nonempty.endswith("= {")
        else 0
    )

    depth = 0
    arguments_depth: int | None = None

    values: dict[str, list[str]] = {}
    program_arguments: list[str] = []

    assignment = re.compile(
        r"^\s*([A-Za-z0-9._-]+)"
        r"\s*=\s*(.*?)\s*$"
    )

    argument_pattern = re.compile(
        r"^(?:[0-9]+\s*=\s*)?"
        r"(.*?)(?:,)?$"
    )

    for line in lines:
        if len(line) > 4096:
            raise MacOSObservationError(
                "LAUNCHD_LINE_LIMIT_EXCEEDED"
            )

        stripped = line.strip()

        if arguments_depth is not None:
            if (
                stripped == "}"
                and depth == arguments_depth
            ):
                arguments_depth = None

            elif depth == arguments_depth:
                argument_match = (
                    argument_pattern.match(
                        stripped
                    )
                )

                if (
                    argument_match is not None
                    and argument_match.group(1)
                ):
                    program_arguments.append(
                        argument_match.group(1)
                    )

        elif (
            depth == service_depth
            and stripped == "arguments = {"
        ):
            arguments_depth = depth + 1

        elif depth == service_depth:
            match = assignment.match(line)

            if match is not None:
                key = match.group(1)
                value = match.group(2)

                values.setdefault(
                    key,
                    [],
                ).append(value)

        depth += stripped.count("{")
        depth -= stripped.count("}")

        if depth < 0:
            raise MacOSObservationError(
                "LAUNCHD_STRUCTURE_MALFORMED"
            )

    if arguments_depth is not None:
        raise MacOSObservationError(
            "LAUNCHD_ARGUMENTS_UNTERMINATED"
        )

    def unique_value(
        *keys: str,
    ) -> str | None:
        found: list[str] = []

        for key in keys:
            found.extend(
                values.get(key, [])
            )

        unique = sorted(set(found))

        if len(unique) > 1:
            raise MacOSObservationError(
                "LAUNCHD_CONFLICTING_FIELD"
            )

        return (
            unique[0]
            if unique
            else None
        )

    state = (
        unique_value("state")
        or "unknown"
    )

    pid_text = unique_value("pid")

    user = unique_value(
        "username",
        "user",
    )

    pid: int | None = None

    if pid_text is not None:
        if not pid_text.isdigit():
            raise MacOSObservationError(
                "LAUNCHD_PID_INVALID"
            )

        pid = int(pid_text)

        if pid <= 0:
            raise MacOSObservationError(
                "LAUNCHD_PID_INVALID"
            )

    return LaunchdObservation(
        identity=identity,
        available=True,
        running=state.lower() == "running",
        pid=pid,
        application_user=user,
        state=state,
        program_arguments=tuple(
            program_arguments
        ),
    )


def parse_lsof_fields(
    stdout: bytes,
    *,
    max_output_bytes: int = 262_144,
) -> tuple[ListenerRecord, ...]:
    text = _bounded_utf8(
        stdout,
        limit=max_output_bytes,
        component="LSOF",
    )

    if len(text.splitlines()) > 8192:
        raise MacOSObservationError(
            "LSOF_LINE_LIMIT_EXCEEDED"
        )

    records: list[ListenerRecord] = []
    current: dict[str, str] | None = None

    def commit() -> None:
        nonlocal current

        if current is None:
            return

        pid_text = current.get("p")
        name = current.get("n")

        if (
            pid_text is None
            or not pid_text.isdigit()
            or int(pid_text) <= 0
            or not name
        ):
            raise MacOSObservationError(
                "LSOF_RECORD_INVALID"
            )

        records.append(
            ListenerRecord(
                pid=int(pid_text),
                command=current.get("c"),
                login=current.get("L"),
                protocol=current.get("P"),
                name=name,
                state=current.get("T"),
            )
        )

        current = None

    for raw_line in text.splitlines():
        line = raw_line.strip("\x00")

        if not line:
            continue

        if len(line) > 4096:
            raise MacOSObservationError(
                "LSOF_LINE_LIMIT_EXCEEDED"
            )

        field = line[0]
        value = line[1:]

        if field == "p":
            commit()
            current = {"p": value}
            continue

        if current is None:
            raise MacOSObservationError(
                "LSOF_FIELD_WITHOUT_PROCESS"
            )

        if field == "T":
            if value.startswith("ST="):
                current["T"] = value[3:]
            continue

        if field in {"c", "L", "P", "n"}:
            current[field] = value

    commit()

    return tuple(
        sorted(
            records,
            key=lambda item: (
                item.pid,
                item.name,
            ),
        )
    )


class MacOSReadOnlyAdapter:
    def __init__(
        self,
        *,
        executor: CommandExecutor,
        http_transport: HttpTransport,
    ) -> None:
        self._executor = executor
        self._http_transport = http_transport

    def inspect_launchd(
        self,
        identity: str,
    ) -> LaunchdObservation:
        if not _LAUNCHD_IDENTITY.fullmatch(identity):
            raise MacOSObservationError(
                "LAUNCHD_IDENTITY_INVALID"
            )

        request = CommandRequest(
            argv=(
                LAUNCHCTL,
                "print",
                identity,
            ),
            timeout_seconds=3.0,
            max_output_bytes=262_144,
        )

        result = self._executor.run(request)

        if result.timed_out:
            raise MacOSObservationError(
                "LAUNCHD_PRINT_TIMEOUT"
            )

        if result.returncode != 0:
            raise MacOSObservationError(
                "LAUNCHD_PRINT_FAILED"
            )

        return parse_launchctl_print(
            identity=identity,
            stdout=result.stdout,
            max_output_bytes=(
                request.max_output_bytes
            ),
        )

    def inspect_listeners(
        self,
        *,
        host: str,
        port: int,
    ) -> tuple[ListenerRecord, ...]:
        if host != "127.0.0.1":
            raise MacOSObservationError(
                "LISTENER_HOST_INVALID"
            )

        if not 1 <= port <= 65_535:
            raise MacOSObservationError(
                "LISTENER_PORT_INVALID"
            )

        request = CommandRequest(
            argv=(
                LSOF,
                "-nP",
                "-a",
                f"-iTCP@{host}:{port}",
                "-sTCP:LISTEN",
                "-FpcLnPT",
            ),
            timeout_seconds=3.0,
            max_output_bytes=262_144,
        )

        result = self._executor.run(request)

        if result.timed_out:
            raise MacOSObservationError(
                "LSOF_TIMEOUT"
            )

        if result.returncode == 1 and not result.stdout:
            return ()

        if result.returncode != 0:
            raise MacOSObservationError(
                "LSOF_FAILED"
            )

        return parse_lsof_fields(
            result.stdout,
            max_output_bytes=(
                request.max_output_bytes
            ),
        )

    def inspect_runtime_filesystem(
        self,
        *,
        runtime_root: str,
        current_link_name: str,
        candidate_runtime: str,
        metadata_filename: str,
        source_marker_filename: str,
        python_relative_path: str,
    ) -> RuntimeFilesystemObservation:
        root = Path(runtime_root)

        if not root.is_absolute():
            raise MacOSObservationError(
                "RUNTIME_ROOT_NOT_ABSOLUTE"
            )

        if (
            Path(current_link_name).name
            != current_link_name
        ):
            raise MacOSObservationError(
                "CURRENT_LINK_NAME_INVALID"
            )

        if not _RUNTIME_ID.fullmatch(candidate_runtime):
            raise MacOSObservationError(
                "CANDIDATE_RUNTIME_INVALID"
            )

        if (
            Path(metadata_filename).name
            != metadata_filename
        ):
            raise MacOSObservationError(
                "METADATA_FILENAME_INVALID"
            )

        if (
            Path(source_marker_filename).name
            != source_marker_filename
        ):
            raise MacOSObservationError(
                "SOURCE_MARKER_FILENAME_INVALID"
            )

        python_relative = _safe_relative_path(
            python_relative_path
        )

        try:
            root_resolved = root.resolve(strict=True)
        except OSError as error:
            raise MacOSObservationError(
                "RUNTIME_ROOT_UNAVAILABLE"
            ) from error

        current_link = root / current_link_name

        if not current_link.is_symlink():
            raise MacOSObservationError(
                "RUNTIME_CURRENT_NOT_SYMLINK"
            )

        try:
            raw_target = os.readlink(current_link)
            target = Path(raw_target)

            if not target.is_absolute():
                target = current_link.parent / target

            resolved_target = target.resolve(strict=True)
            resolved_target.relative_to(root_resolved)
        except (OSError, ValueError) as error:
            raise MacOSObservationError(
                "RUNTIME_CURRENT_ESCAPED_ROOT"
            ) from error

        current_runtime = resolved_target.name

        candidate_root = (
            root
            / "venvs"
            / candidate_runtime
        )

        candidate_available = (
            candidate_root.is_dir()
            and not candidate_root.is_symlink()
        )

        if not candidate_available:
            raise MacOSObservationError(
                "CANDIDATE_RUNTIME_UNAVAILABLE"
            )

        try:
            candidate_resolved = (
                candidate_root.resolve(strict=True)
            )

            candidate_resolved.relative_to(
                root_resolved
            )
        except (OSError, ValueError) as error:
            raise MacOSObservationError(
                "CANDIDATE_RUNTIME_ESCAPED_ROOT"
            ) from error

        metadata_path = (
            candidate_root
            / metadata_filename
        )

        marker_path = (
            candidate_root
            / source_marker_filename
        )

        metadata_bytes = _bounded_read(
            metadata_path,
            limit=262_144,
            component="RUNTIME_METADATA",
        )

        marker_bytes = _bounded_read(
            marker_path,
            limit=1024,
            component="SOURCE_MARKER",
        )

        try:
            metadata = json.loads(
                metadata_bytes.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise MacOSObservationError(
                "RUNTIME_METADATA_INVALID"
            ) from error

        if not isinstance(metadata, dict):
            raise MacOSObservationError(
                "RUNTIME_METADATA_INVALID"
            )

        try:
            source_commit = marker_bytes.decode(
                "utf-8"
            ).strip()
        except UnicodeDecodeError as error:
            raise MacOSObservationError(
                "SOURCE_MARKER_INVALID"
            ) from error

        if not _COMMIT_ID.fullmatch(source_commit):
            raise MacOSObservationError(
                "SOURCE_MARKER_INVALID"
            )

        python_path = candidate_root.joinpath(
            *python_relative.parts
        )

        if not python_path.is_file():
            raise MacOSObservationError(
                "RUNTIME_PYTHON_UNAVAILABLE"
            )

        return RuntimeFilesystemObservation(
            current_runtime=current_runtime,
            candidate_runtime=candidate_runtime,
            candidate_available=True,
            metadata=metadata,
            source_marker_commit=source_commit,
            python_executable=str(python_path),
        )

    def probe_runtime_python(
        self,
        executable: str,
    ) -> RuntimePythonObservation:
        path = Path(executable)

        if not path.is_absolute():
            raise MacOSObservationError(
                "RUNTIME_PYTHON_NOT_ABSOLUTE"
            )

        request = CommandRequest(
            argv=(
                executable,
                "-I",
                "-S",
                "--version",
            ),
            timeout_seconds=3.0,
            max_output_bytes=4096,
            env={},
        )

        result = self._executor.run(request)

        if result.timed_out:
            raise MacOSObservationError(
                "RUNTIME_PYTHON_TIMEOUT"
            )

        if result.returncode != 0:
            raise MacOSObservationError(
                "RUNTIME_PYTHON_FAILED"
            )

        combined = (
            result.stdout
            + b"\n"
            + result.stderr
        )

        text = _bounded_utf8(
            combined,
            limit=request.max_output_bytes,
            component="RUNTIME_PYTHON",
        )

        version_lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if (
            len(version_lines) != 1
            or _PYTHON_VERSION.match(
                version_lines[0]
            )
            is None
        ):
            raise MacOSObservationError(
                "RUNTIME_PYTHON_VERSION_INVALID"
            )

        return RuntimePythonObservation(
            executable=executable,
            version=version_lines[0],
            returncode=result.returncode,
        )

    def probe_http(
        self,
        request: HttpProbeRequest,
    ) -> HttpProbeResponse:
        return self._http_transport.probe(
            request
        )


__all__ = (
    "LAUNCHCTL",
    "LSOF",
    "LaunchdObservation",
    "ListenerRecord",
    "MacOSObservationError",
    "MacOSReadOnlyAdapter",
    "RuntimeFilesystemObservation",
    "RuntimePythonObservation",
    "StdlibHttpTransport",
    "SubprocessCommandExecutor",
    "parse_launchctl_print",
    "parse_lsof_fields",
)
