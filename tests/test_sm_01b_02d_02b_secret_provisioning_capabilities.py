from __future__ import annotations

import inspect
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from ops.macos.shopping.secret_provisioning_adapters import MutationOutcome
from ops.macos.shopping.secret_provisioning_capabilities import (
    AGE,
    AGE_KEYGEN,
    BREW,
    ConcreteCreateControlPlaneAgeIdentity,
    ConcreteEnsureAgeTooling,
    ConcreteEnsureSopsTool,
    ConcreteIntakeOfflineRecoveryPublicRecipient,
    ConcreteRegisterControlPlaneRecipientMetadata,
    ConcreteRegisterOfflineRecoveryPublicMetadata,
    OfflineRecoveryPublicRecipient,
)
from ops.macos.shopping.secret_provisioning_observations import executable_present

ROOT = Path(__file__).resolve().parents[1]
VALID_RECIPIENT = "age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq5cu47z"


def metadata() -> dict[str, object]:
    return json.loads((ROOT / "config/shopping-secret-backend.json").read_text())


def intake_policy() -> dict[str, object]:
    return json.loads(
        (ROOT / "config/shopping-secret-provisioning.json").read_text()
    )["offline_recovery_intake_policy"]


def make_safe_parents(path: Path, home: Path) -> None:
    path.parent.mkdir(parents=True, mode=0o700)
    current = path.parent
    while current != home:
        current.chmod(0o700)
        current = current.parent


class Runner:
    def __init__(self, *, returncode: int = 0, raises: bool = False,
                 output: bytes = b"", before_call=None) -> None:
        self.returncode = returncode; self.raises = raises; self.output = output
        self.before_call = before_call; self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if self.before_call: self.before_call()
        if self.raises: raise TimeoutError
        if self.output and hasattr(kwargs["stdout"], "write"): kwargs["stdout"].write(self.output)
        return SimpleNamespace(returncode=self.returncode)


@pytest.mark.parametrize("capability,method", [
    (ConcreteEnsureSopsTool, "ensure_sops_tool"),
    (ConcreteEnsureAgeTooling, "ensure_age_tooling"),
    (ConcreteCreateControlPlaneAgeIdentity, "create_control_plane_age_identity"),
    (ConcreteRegisterControlPlaneRecipientMetadata, "register_control_plane_recipient_metadata"),
    (ConcreteRegisterOfflineRecoveryPublicMetadata, "register_offline_recovery_public_metadata"),
    (ConcreteIntakeOfflineRecoveryPublicRecipient, "intake_offline_recovery_public_recipient"),
])
def test_exact_protocol_method_is_zero_arg(capability, method) -> None:
    assert list(inspect.signature(getattr(capability, method)).parameters) == ["self"]
    assert not any(name in capability.__dict__ for name in ("run", "execute", "invoke", "command"))


@pytest.mark.parametrize("kind,formula,required", [(ConcreteEnsureSopsTool, "sops", 1), (ConcreteEnsureAgeTooling, "age", 2)])
def test_fixed_tool_command_one_launch_and_postcondition(kind, formula, required) -> None:
    runner = Runner()
    def observe(path):
        if path == BREW: return True
        return bool(runner.calls)
    capability = kind(process_runner=runner, executable_observer=observe)
    method = capability.ensure_sops_tool if formula == "sops" else capability.ensure_age_tooling
    assert method() is MutationOutcome.COMPLETED
    assert len(runner.calls) == 1
    argv, options = runner.calls[0]
    assert argv == ("/opt/homebrew/bin/brew", "install", formula)
    assert options["shell"] is False and options["env"] == {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}


def test_tools_already_ready_launch_nothing() -> None:
    runner = Runner()
    assert ConcreteEnsureSopsTool(process_runner=runner, executable_observer=lambda _: True).ensure_sops_tool() is MutationOutcome.COMPLETED
    assert runner.calls == []


@pytest.mark.parametrize("runner", [Runner(returncode=1), Runner(raises=True)])
def test_tool_failure_after_launch_is_uncertain_without_retry(runner) -> None:
    values = iter((False, True))
    capability = ConcreteEnsureSopsTool(process_runner=runner, executable_observer=lambda path: True if path == BREW else next(values))
    assert capability.ensure_sops_tool() is MutationOutcome.UNCERTAIN
    assert len(runner.calls) == 1


def test_tool_unsafe_precondition_is_failed() -> None:
    runner = Runner()
    assert ConcreteEnsureSopsTool(process_runner=runner, executable_observer=lambda _: False).ensure_sops_tool() is MutationOutcome.FAILED
    assert runner.calls == []


def test_identity_exclusive_atomic_creation_and_no_content_evidence(tmp_path: Path) -> None:
    runner = Runner(output=b"AGE-SECRET-KEY-TEST-PRIVATE\n")
    capability = ConcreteCreateControlPlaneAgeIdentity(control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(), process_runner=runner, executable_observer=lambda path: path == AGE_KEYGEN)
    outcome = capability.create_control_plane_age_identity()
    destination = tmp_path / ".config/sops/age/keys.txt"
    assert outcome is MutationOutcome.COMPLETED and destination.exists()
    assert stat_mode(destination) == 0o600
    current = destination.parent
    while current != tmp_path:
        assert stat_mode(current) == 0o700
        current = current.parent
    assert len(runner.calls) == 1 and runner.calls[0][0] == (str(AGE_KEYGEN),)
    assert not list(destination.parent.glob(".*.tmp-*"))
    assert "AGE-SECRET" not in json.dumps(outcome.value)


def stat_mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


def test_identity_never_overwrites_and_rejects_symlink(tmp_path: Path) -> None:
    destination = tmp_path / ".config/sops/age/keys.txt"; make_safe_parents(destination, tmp_path); destination.write_bytes(b"existing"); destination.chmod(0o600)
    runner = Runner()
    capability = ConcreteCreateControlPlaneAgeIdentity(control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(), process_runner=runner, executable_observer=lambda _: True)
    assert capability.create_control_plane_age_identity() is MutationOutcome.COMPLETED and runner.calls == []
    destination.unlink(); destination.symlink_to(tmp_path / "elsewhere")
    assert capability.create_control_plane_age_identity() is MutationOutcome.FAILED and runner.calls == []


def test_control_plane_recipient_direct_redirection_is_value_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ops.macos.shopping.secret_provisioning_capabilities.uuid.uuid4",
        lambda: SimpleNamespace(hex="fixed"),
    )
    identity = tmp_path / ".config/sops/age/keys.txt"; make_safe_parents(identity, tmp_path); identity.write_bytes(b"private-not-read-by-runner"); identity.chmod(0o600)
    runner = Runner(output=b"age1qqqqqqqqqqqqqq\n")
    capability = ConcreteRegisterControlPlaneRecipientMetadata(control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(), process_runner=runner, executable_observer=lambda _: True)
    outcome = capability.register_control_plane_recipient_metadata()
    assert outcome is MutationOutcome.COMPLETED and len(runner.calls) == 2
    assert runner.calls[0][0] == (str(AGE_KEYGEN), "-y", str(identity))
    expected_recipient_file = tmp_path / ".config/aicontrolcenter/shopping-secrets/recipients/.control-plane.txt.tmp-fixed"
    assert runner.calls[1][0] == (
        "/opt/homebrew/bin/age", "--encrypt", "--recipients-file",
        str(expected_recipient_file),
    )
    assert runner.calls[1][1]["shell"] is False
    assert runner.calls[1][1]["stdin"] is subprocess.DEVNULL
    assert runner.calls[1][1]["stdout"] is subprocess.DEVNULL
    assert runner.calls[1][1]["stderr"] is subprocess.DEVNULL
    assert "age1" not in json.dumps(outcome.value)


def test_offline_recovery_is_public_only_and_atomic(tmp_path: Path) -> None:
    source = tmp_path / ".config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt"; make_safe_parents(source, tmp_path); source.write_bytes(b"age1qqqqqqqqqqqqqq\n"); source.chmod(0o600)
    capability = ConcreteRegisterOfflineRecoveryPublicMetadata(control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(), process_runner=Runner(), executable_observer=lambda path: path == AGE)
    signature = inspect.signature(capability.__init__)
    assert not any("private" in name or "identity" in name for name in signature.parameters)
    assert capability.register_offline_recovery_public_metadata() is MutationOutcome.COMPLETED
    destination = tmp_path / ".config/aicontrolcenter/shopping-secrets/recipients/offline-recovery.txt"
    assert destination.exists() and stat_mode(destination) == 0o600 and stat_mode(destination.parent) == 0o700
    assert not list(destination.parent.glob(".*.tmp-*"))


def intake_capability(tmp_path: Path, *, runner: Runner | None = None):
    destination = tmp_path / ".config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt"
    make_safe_parents(destination, tmp_path)
    return ConcreteIntakeOfflineRecoveryPublicRecipient(
        control_plane_home=tmp_path, intake_policy=intake_policy(),
        expected_uid=os.getuid(), expected_gid=os.getgid(),
        public_recipient=OfflineRecoveryPublicRecipient(VALID_RECIPIENT),
        process_runner=runner or Runner(), executable_observer=lambda path: path == AGE,
    ), destination


def test_typed_public_recipient_boundary_is_exact_and_value_free() -> None:
    value = OfflineRecoveryPublicRecipient(VALID_RECIPIENT)
    assert "age1" not in repr(value) and "age1" not in str(value)
    for invalid in ("", "age1bad", VALID_RECIPIENT + "\n", VALID_RECIPIENT + " extra",
                    VALID_RECIPIENT + "\n" + VALID_RECIPIENT):
        with pytest.raises(ValueError, match="^INVALID_OFFLINE_RECOVERY_PUBLIC_RECIPIENT$") as error:
            OfflineRecoveryPublicRecipient(invalid)
        if invalid:
            assert invalid not in str(error.value)


def test_intake_fixed_target_no_clobber_and_fixed_age_validation(tmp_path: Path) -> None:
    destination = tmp_path / ".config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt"
    destination_states: list[bool] = []
    runner = Runner(before_call=lambda: destination_states.append(destination.exists()))
    capability, destination = intake_capability(tmp_path, runner=runner)
    assert capability.intake_offline_recovery_public_recipient() is MutationOutcome.COMPLETED
    assert destination_states == [False]
    assert destination.read_text() == VALID_RECIPIENT + "\n"
    assert stat_mode(destination) == 0o600
    assert runner.calls[0][0] == (
        str(AGE), "--encrypt", "--recipient", VALID_RECIPIENT
    )
    options = runner.calls[0][1]
    assert options["shell"] is False
    assert options["stdin"] is subprocess.DEVNULL
    assert options["stdout"] is subprocess.DEVNULL
    assert options["stderr"] is subprocess.DEVNULL
    assert options["env"] == {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}
    original = destination.read_bytes()
    assert capability.intake_offline_recovery_public_recipient() is MutationOutcome.FAILED
    assert destination.read_bytes() == original and len(runner.calls) == 2


def test_intake_requires_safe_existing_owned_parent_chain(tmp_path: Path) -> None:
    destination = tmp_path / ".config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt"
    capability = ConcreteIntakeOfflineRecoveryPublicRecipient(
        control_plane_home=tmp_path, intake_policy=intake_policy(),
        expected_uid=os.getuid(), expected_gid=os.getgid(),
        public_recipient=OfflineRecoveryPublicRecipient(VALID_RECIPIENT),
        process_runner=Runner(), executable_observer=lambda _: True,
    )
    assert capability.intake_offline_recovery_public_recipient() is MutationOutcome.FAILED
    assert not destination.exists()
    unsafe = tmp_path / ".config"
    unsafe.symlink_to(tmp_path / "elsewhere", target_is_directory=True)
    assert capability.intake_offline_recovery_public_recipient() is MutationOutcome.FAILED


def test_intake_rejects_symlink_target_and_preserves_no_clobber(tmp_path: Path) -> None:
    capability, destination = intake_capability(tmp_path)
    elsewhere = tmp_path / "elsewhere"; elsewhere.write_text("public"); elsewhere.chmod(0o600)
    destination.symlink_to(elsewhere)
    assert capability.intake_offline_recovery_public_recipient() is MutationOutcome.FAILED
    destination.unlink(); destination.write_text("existing"); destination.chmod(0o644)
    assert capability.intake_offline_recovery_public_recipient() is MutationOutcome.FAILED
    assert stat_mode(destination) == 0o644


@pytest.mark.parametrize("runner", [Runner(returncode=1), Runner(raises=True)])
def test_intake_prevalidation_failure_is_failed_without_mutation(
    tmp_path: Path, runner: Runner,
) -> None:
    capability, destination = intake_capability(tmp_path, runner=runner)
    assert capability.intake_offline_recovery_public_recipient() is MutationOutcome.FAILED
    assert not destination.exists()
    assert len(runner.calls) == 1


def test_intake_rejects_unsafe_parent_mode(tmp_path: Path) -> None:
    capability, destination = intake_capability(tmp_path)
    destination.parent.chmod(0o755)
    assert capability.intake_offline_recovery_public_recipient() is MutationOutcome.FAILED
    assert not destination.exists()


def test_intake_rejects_broadened_policy_and_wrong_gid(tmp_path: Path) -> None:
    capability, destination = intake_capability(tmp_path)
    broadened = intake_policy(); broadened["relative_path"] = "arbitrary.txt"
    rejected = ConcreteIntakeOfflineRecoveryPublicRecipient(
        control_plane_home=tmp_path, intake_policy=broadened,
        expected_uid=os.getuid(), expected_gid=os.getgid(),
        public_recipient=OfflineRecoveryPublicRecipient(VALID_RECIPIENT),
        process_runner=Runner(), executable_observer=lambda _: True,
    )
    assert rejected.intake_offline_recovery_public_recipient() is MutationOutcome.FAILED
    wrong_gid = ConcreteIntakeOfflineRecoveryPublicRecipient(
        control_plane_home=tmp_path, intake_policy=intake_policy(),
        expected_uid=os.getuid(), expected_gid=os.getgid() + 1,
        public_recipient=OfflineRecoveryPublicRecipient(VALID_RECIPIENT),
        process_runner=Runner(), executable_observer=lambda _: True,
    )
    assert wrong_gid.intake_offline_recovery_public_recipient() is MutationOutcome.FAILED
    assert not destination.exists()

    wrong_uid = ConcreteIntakeOfflineRecoveryPublicRecipient(
        control_plane_home=tmp_path, intake_policy=intake_policy(),
        expected_uid=os.getuid() + 1, expected_gid=os.getgid(),
        public_recipient=OfflineRecoveryPublicRecipient(VALID_RECIPIENT),
        process_runner=Runner(), executable_observer=lambda _: True,
    )
    assert wrong_uid.intake_offline_recovery_public_recipient() is MutationOutcome.FAILED
    assert not destination.exists()


def test_intake_ambiguity_after_creation_is_uncertain_without_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    capability, destination = intake_capability(tmp_path)
    monkeypatch.setattr(
        "ops.macos.shopping.secret_provisioning_capabilities.os.write",
        lambda descriptor, payload: (_ for _ in ()).throw(OSError("injected write failure")),
    )
    assert capability.intake_offline_recovery_public_recipient() is MutationOutcome.UNCERTAIN
    assert destination.exists()


def test_intake_parent_rebind_after_creation_is_uncertain_without_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    capability, destination = intake_capability(tmp_path)
    original_parent = destination.parent
    displaced_parent = original_parent.with_name("inbox-created-by-mutation")
    real_fsync = os.fsync

    def rebind_after_write(descriptor: int) -> None:
        real_fsync(descriptor)
        original_parent.rename(displaced_parent)
        original_parent.mkdir(mode=0o700)
        replacement = original_parent / destination.name
        replacement.write_bytes(b"safe-looking-replacement\n")
        replacement.chmod(0o600)

    monkeypatch.setattr(os, "fsync", rebind_after_write)
    assert capability.intake_offline_recovery_public_recipient() is MutationOutcome.UNCERTAIN
    created = displaced_parent / destination.name
    assert created.exists()
    assert created.read_text() == VALID_RECIPIENT + "\n"
    assert destination.read_bytes() == b"safe-looking-replacement\n"


@pytest.mark.parametrize("kind", [
    ConcreteCreateControlPlaneAgeIdentity,
    ConcreteRegisterControlPlaneRecipientMetadata,
    ConcreteRegisterOfflineRecoveryPublicMetadata,
])
def test_expected_uid_is_required_without_ambient_fallback(tmp_path: Path, kind) -> None:
    with pytest.raises(TypeError):
        kind(control_plane_home=tmp_path, backend_metadata=metadata())
    source = inspect.getsource(kind)
    assert "getuid" not in source and "getenv" not in source and "HOME" not in source


@pytest.mark.parametrize("home_factory", [
    lambda path: Path("relative-home"),
    lambda path: (path / "missing"),
])
def test_control_plane_home_must_be_absolute_existing_and_safe(tmp_path: Path, home_factory) -> None:
    capability = ConcreteCreateControlPlaneAgeIdentity(
        control_plane_home=home_factory(tmp_path), backend_metadata=metadata(),
        expected_uid=os.getuid(), process_runner=Runner(), executable_observer=lambda _: True,
    )
    assert capability.create_control_plane_age_identity() is MutationOutcome.FAILED


def test_control_plane_home_symlink_and_wrong_owner_are_rejected(tmp_path: Path) -> None:
    link = tmp_path / "home-link"; link.symlink_to(tmp_path, target_is_directory=True)
    for home, uid in ((link, os.getuid()), (tmp_path, os.getuid() + 1)):
        capability = ConcreteCreateControlPlaneAgeIdentity(
            control_plane_home=home, backend_metadata=metadata(), expected_uid=uid,
            process_runner=Runner(), executable_observer=lambda _: True,
        )
        assert capability.create_control_plane_age_identity() is MutationOutcome.FAILED


def test_owned_0755_home_is_allowed_but_unsafe_secret_parent_is_not(tmp_path: Path) -> None:
    tmp_path.chmod(0o755)
    runner = Runner(output=b"private")
    capability = ConcreteCreateControlPlaneAgeIdentity(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=runner, executable_observer=lambda _: True,
    )
    assert capability.create_control_plane_age_identity() is MutationOutcome.COMPLETED
    destination = tmp_path / ".config/sops/age/keys.txt"
    destination.unlink()
    (tmp_path / ".config").chmod(0o755)
    assert capability.create_control_plane_age_identity() is MutationOutcome.FAILED


def test_unsafe_intermediate_parent_is_rejected_without_launch(tmp_path: Path) -> None:
    unsafe = tmp_path / ".config"; unsafe.mkdir(mode=0o755); unsafe.chmod(0o755)
    runner = Runner(output=b"private")
    capability = ConcreteCreateControlPlaneAgeIdentity(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=runner, executable_observer=lambda _: True,
    )
    assert capability.create_control_plane_age_identity() is MutationOutcome.FAILED
    assert runner.calls == []


def test_fixed_executable_safe_symlink_broken_and_unsafe_target(tmp_path: Path) -> None:
    target = tmp_path / "tool"; target.write_text("tool"); target.chmod(0o700)
    safe_link = tmp_path / "safe"; safe_link.symlink_to(target)
    broken = tmp_path / "broken"; broken.symlink_to(tmp_path / "absent")
    directory = tmp_path / "directory"; directory.mkdir(mode=0o700)
    unsafe = tmp_path / "unsafe"; unsafe.symlink_to(directory)
    assert executable_present(safe_link) is False
    assert executable_present(broken) is False
    assert executable_present(unsafe) is False


def test_recipient_file_must_contain_exactly_one_record_even_if_age_accepts(tmp_path: Path) -> None:
    source = tmp_path / ".config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt"
    make_safe_parents(source, tmp_path)
    source.write_bytes(b"age1source\nage1other\n")
    source.chmod(0o600)
    runner = Runner(returncode=0)
    capability = ConcreteRegisterOfflineRecoveryPublicMetadata(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=runner, executable_observer=lambda _: True,
    )
    assert capability.register_offline_recovery_public_metadata() is MutationOutcome.FAILED
    assert runner.calls == []


@pytest.mark.parametrize("value", [
    b"# comment\nage1source\n", b"age1source\n# comment\n", b"ssh-ed25519 AAAA\n",
    b"age1source\r\n", b"age1" + b"q" * 1021,
])
def test_recipient_structural_rejections_are_value_free(tmp_path: Path, value: bytes) -> None:
    source = tmp_path / ".config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt"
    make_safe_parents(source, tmp_path); source.write_bytes(value); source.chmod(0o600)
    runner = Runner(returncode=0)
    capability = ConcreteRegisterOfflineRecoveryPublicMetadata(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=runner, executable_observer=lambda _: True,
    )
    outcome = capability.register_offline_recovery_public_metadata()
    assert outcome is MutationOutcome.FAILED and runner.calls == []
    assert value.decode("ascii", errors="ignore") not in json.dumps(outcome.value)


def test_parent_mutation_then_chmod_error_is_uncertain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_chmod = os.chmod
    def fail_after_mkdir(path, mode, **kwargs):
        if Path(path) == tmp_path / ".config":
            raise OSError("injected")
        return real_chmod(path, mode, **kwargs)
    monkeypatch.setattr(os, "chmod", fail_after_mkdir)
    capability = ConcreteCreateControlPlaneAgeIdentity(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=Runner(output=b"private"), executable_observer=lambda _: True,
    )
    assert capability.create_control_plane_age_identity() is MutationOutcome.UNCERTAIN


def test_temp_file_mutation_then_wrapper_error_is_uncertain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(os, "fdopen", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("injected")))
    capability = ConcreteCreateControlPlaneAgeIdentity(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=Runner(output=b"private"), executable_observer=lambda _: True,
    )
    assert capability.create_control_plane_age_identity() is MutationOutcome.UNCERTAIN
    assert list(tmp_path.rglob("*.tmp-*")) == []


def test_atomic_no_clobber_collision_preserves_existing_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = Runner(output=b"new-private")
    destination = tmp_path / ".config/sops/age/keys.txt"
    real_link = os.link
    def collide(source, target, **kwargs):
        Path(target).write_bytes(b"racing-existing")
        Path(target).chmod(0o600)
        return real_link(source, target, **kwargs)
    monkeypatch.setattr(os, "link", collide)
    capability = ConcreteCreateControlPlaneAgeIdentity(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=runner, executable_observer=lambda _: True,
    )
    assert capability.create_control_plane_age_identity() is MutationOutcome.UNCERTAIN
    assert destination.read_bytes() == b"racing-existing"


def test_fake_printable_age_recipient_is_rejected_semantically(tmp_path: Path) -> None:
    source = tmp_path / ".config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt"
    make_safe_parents(source, tmp_path); source.write_bytes(b"age1printablebutfake\n"); source.chmod(0o600)
    capability = ConcreteRegisterOfflineRecoveryPublicMetadata(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=Runner(returncode=1), executable_observer=lambda _: True,
    )
    assert capability.register_offline_recovery_public_metadata() is MutationOutcome.FAILED


def test_existing_control_plane_recipient_requires_exact_identity_binding(tmp_path: Path) -> None:
    identity = tmp_path / ".config/sops/age/keys.txt"
    destination = tmp_path / ".config/aicontrolcenter/shopping-secrets/recipients/control-plane.txt"
    for path, value in ((identity, b"private-never-read"), (destination, b"age1existing\n")):
        make_safe_parents(path, tmp_path); path.write_bytes(value); path.chmod(0o600)
    mismatched = Runner(output=b"age1different\n")
    capability = ConcreteRegisterControlPlaneRecipientMetadata(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=mismatched, executable_observer=lambda _: True,
    )
    assert capability.register_control_plane_recipient_metadata() is MutationOutcome.UNCERTAIN
    assert destination.read_bytes() == b"age1existing\n"
    assert list(destination.parent.glob(f".{destination.name}.tmp-*")) == []
    assert len(mismatched.calls) == 2
    assert len([call for call in mismatched.calls if call[0] == (str(AGE_KEYGEN), "-y", str(identity))]) == 1
    matching = Runner(output=b"age1existing\n")
    capability = ConcreteRegisterControlPlaneRecipientMetadata(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=matching, executable_observer=lambda _: True,
    )
    assert capability.register_control_plane_recipient_metadata() is MutationOutcome.COMPLETED
    derive = [call for call in matching.calls if call[0][0] == str(AGE_KEYGEN)][0]
    assert derive[0] == (str(AGE_KEYGEN), "-y", str(identity))
    assert derive[1]["stdin"] is not identity


def test_offline_existing_destination_requires_content_equivalence(tmp_path: Path) -> None:
    source = tmp_path / ".config/aicontrolcenter/shopping-secrets/inbox/offline-recovery.txt"
    destination = tmp_path / ".config/aicontrolcenter/shopping-secrets/recipients/offline-recovery.txt"
    for path, value in ((source, b"age1source\n"), (destination, b"age1other\n")):
        make_safe_parents(path, tmp_path); path.write_bytes(value); path.chmod(0o600)
    capability = ConcreteRegisterOfflineRecoveryPublicMetadata(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=Runner(), executable_observer=lambda _: True,
    )
    assert capability.register_offline_recovery_public_metadata() is MutationOutcome.FAILED


def test_private_identity_is_never_opened_by_python(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    identity = tmp_path / ".config/sops/age/keys.txt"
    make_safe_parents(identity, tmp_path); identity.write_bytes(b"private-value"); identity.chmod(0o600)
    original_open = Path.open
    def guarded_open(path, *args, **kwargs):
        if path == identity: raise AssertionError("private identity read")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded_open)
    capability = ConcreteRegisterControlPlaneRecipientMetadata(
        control_plane_home=tmp_path, backend_metadata=metadata(), expected_uid=os.getuid(),
        process_runner=Runner(output=b"age1derived\n"), executable_observer=lambda _: True,
    )
    assert capability.register_control_plane_recipient_metadata() is MutationOutcome.COMPLETED


def test_portable_value_free_metadata_and_dependency_boundaries() -> None:
    raw = (ROOT / "config/shopping-secret-backend.json").read_text()
    assert "/Users/" not in raw and "AGE-SECRET-KEY" not in raw and '"recipient_value"' not in raw
    source = (ROOT / "ops/macos/shopping/secret_provisioning_capabilities.py").read_text().lower()
    assert not any(token in source for token in ("docker", "colima", "mariadb", "ubuntu", "wordpress", "woocommerce"))
    core = "\n".join(path.read_text() for path in (ROOT / "core").rglob("*.py"))
    assert "from ops." not in core and "import ops." not in core
