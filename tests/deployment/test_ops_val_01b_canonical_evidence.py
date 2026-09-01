from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "ops/macos/validation/run-deployment-regression-gate.sh"
HELPER = ROOT / "ops/macos/validation/canonical_evidence.py"
INVOCATION_ID = "a" * 32

spec = importlib.util.spec_from_file_location("canonical_evidence", HELPER)
assert spec and spec.loader
canonical_evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(canonical_evidence)


class CanonicalEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.paths: list[Path] = []

    def tearDown(self) -> None:
        for path in self.paths:
            shutil.rmtree(path)

    def evidence_directory(self) -> Path:
        path = Path(
            tempfile.mkdtemp(
                prefix="aicontrolcenter-canonical-evidence.",
                dir="/private/tmp",
            )
        )
        path.chmod(0o700)
        self.paths.append(path)
        return path

    def finalize(
        self,
        output: str,
        status: int,
        capture_status: int = 0,
        invocation_id: str = INVOCATION_ID,
    ) -> tuple[Path, dict[str, object]]:
        directory = self.evidence_directory()
        (directory / "pytest.log").write_text(output, encoding="utf-8")
        result = canonical_evidence.finalize_evidence(
            directory,
            status,
            capture_status,
            invocation_id,
            ["-q"],
        )
        return directory, result

    def test_success_preserves_exact_status_summary_and_invocation(self) -> None:
        directory, result = self.finalize(
            "................................ [100%]\n"
            "12 passed, 3 warnings in 1.25s\n",
            0,
        )
        self.assertEqual((directory / "exit-status").read_text(), "0\n")
        self.assertEqual(result["schema_version"], "ops-val-01b/canonical-evidence/v2")
        self.assertEqual(result["invocation_id"], INVOCATION_ID)
        self.assertEqual(result["exit_status"], 0)
        self.assertEqual(result["capture_exit_status"], 0)
        self.assertEqual(
            result["pytest_summary"],
            "12 passed, 3 warnings in 1.25s",
        )
        self.assertEqual(result["state"], "COMPLETED_PASS")
        self.assertIs(result["completed"], True)
        self.assertIs(result["validated_pass"], True)

    def test_failed_run_preserves_nonzero_status(self) -> None:
        directory, result = self.finalize(
            "1 failed, 11 passed in 0.42s\n",
            1,
        )
        self.assertEqual((directory / "exit-status").read_text(), "1\n")
        self.assertEqual(result["exit_status"], 1)
        self.assertEqual(
            result["pytest_summary"],
            "1 failed, 11 passed in 0.42s",
        )
        self.assertEqual(result["state"], "COMPLETED_FAIL")
        self.assertIs(result["completed"], True)
        self.assertIs(result["validated_pass"], False)

    def test_failure_summary_with_zero_exit_cannot_become_pass(self) -> None:
        directory, result = self.finalize(
            "1 failed, 11 passed in 0.42s\n",
            0,
        )
        self.assertEqual(result["state"], "COMPLETED_FAIL")
        self.assertIs(result["validated_pass"], False)
        completed = subprocess.run(
            [
                sys.executable,
                str(HELPER),
                str(directory),
                "0",
                "0",
                INVOCATION_ID,
                "--",
                "-q",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 4)

    def test_error_summary_with_zero_exit_cannot_become_pass(self) -> None:
        _, result = self.finalize(
            "1 error, 11 passed in 0.42s\n",
            0,
        )
        self.assertEqual(result["state"], "COMPLETED_FAIL")
        self.assertIs(result["validated_pass"], False)

    def test_partial_or_missing_summary_is_capture_uncertain(self) -> None:
        for output in (
            "tests/test_example.py .... [  4%]\n",
            "collection complete\n",
        ):
            with self.subTest(output=output):
                directory, result = self.finalize(output, 0)
                self.assertIsNone(result["pytest_summary"])
                self.assertEqual(result["state"], "CAPTURE_UNCERTAIN")
                self.assertIs(result["completed"], False)
                self.assertIs(result["validated_pass"], False)
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(HELPER),
                        str(directory),
                        "0",
                        "0",
                        INVOCATION_ID,
                        "--",
                        "-q",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 4)

    def test_capture_failure_cannot_coexist_with_validated_pass(self) -> None:
        directory, result = self.finalize(
            "12 passed, 3 warnings in 1.25s\n",
            0,
            capture_status=1,
        )
        self.assertEqual(result["capture_exit_status"], 1)
        self.assertEqual(result["state"], "CAPTURE_UNCERTAIN")
        self.assertIs(result["completed"], False)
        self.assertIs(result["validated_pass"], False)
        completed = subprocess.run(
            [
                sys.executable,
                str(HELPER),
                str(directory),
                "0",
                "1",
                INVOCATION_ID,
                "--",
                "-q",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 4)

    def test_zero_actual_passes_cannot_become_validated_pass(self) -> None:
        _, result = self.finalize(
            "2 skipped, 3 deselected in 0.03s\n",
            0,
        )
        self.assertEqual(result["state"], "COMPLETED_FAIL")
        self.assertIs(result["validated_pass"], False)

    def test_invalid_invocation_id_is_rejected(self) -> None:
        directory = self.evidence_directory()
        (directory / "pytest.log").write_text(
            "1 passed in 0.01s\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            ValueError,
            "invalid canonical invocation id",
        ):
            canonical_evidence.finalize_evidence(
                directory,
                0,
                0,
                "not-an-invocation-id",
                ["-q"],
            )

    def test_evidence_finalization_failure_is_fail_closed(self) -> None:
        directory = self.evidence_directory()
        directory.chmod(0o755)
        with self.assertRaisesRegex(
            ValueError,
            "mode must be 0700",
        ):
            canonical_evidence.finalize_evidence(
                directory,
                0,
                0,
                INVOCATION_ID,
                ["-q"],
            )

    def test_artifacts_are_outside_worktree_and_json_is_deterministic(self) -> None:
        directory, result = self.finalize(
            "2 passed, 1 subtest passed in 0.03s\n",
            0,
        )
        payload = json.loads((directory / "result.json").read_text())
        self.assertNotIn(ROOT, directory.parents)
        self.assertEqual(payload, result)
        self.assertEqual(
            result,
            {
                "schema_version": "ops-val-01b/canonical-evidence/v2",
                "invocation_id": INVOCATION_ID,
                "canonical_command": (
                    "ops/macos/validation/"
                    "run-deployment-regression-gate.sh -q"
                ),
                "state": "COMPLETED_PASS",
                "completed": True,
                "capture_exit_status": 0,
                "exit_status": 0,
                "pytest_summary": (
                    "2 passed, 1 subtest passed in 0.03s"
                ),
                "validated_pass": True,
            },
        )
        self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual(directory.stat().st_uid, os.getuid())

    def test_distinct_invocations_are_bound_in_result_json(self) -> None:
        first_directory, first = self.finalize(
            "1 passed in 0.01s\n",
            0,
            invocation_id="a" * 32,
        )
        second_directory, second = self.finalize(
            "1 passed in 0.01s\n",
            0,
            invocation_id="b" * 32,
        )
        self.assertNotEqual(first_directory, second_directory)
        self.assertEqual(first["invocation_id"], "a" * 32)
        self.assertEqual(second["invocation_id"], "b" * 32)
        self.assertNotEqual(
            first["invocation_id"],
            second["invocation_id"],
        )

    def test_runner_keeps_canonical_command_and_has_no_bypass_override(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertRegex(
            source,
            r'"\$PYTHON" \\\n\s+-m pytest "\$@"',
        )
        self.assertIn("AICONTROLCENTER_TEST_PYTHON", source)
        self.assertIn('pytest "$@"', source)
        self.assertIn("CANONICAL_INVOCATION_ID=", source)
        self.assertIn('"$TEE_STATUS"', source)
        self.assertIn('"$INVOCATION_ID"', source)
        self.assertIsNone(
            re.search(
                r"(?:SKIP|BYPASS|COMMAND|PYTEST_ARGS)=",
                source,
            )
        )


if __name__ == "__main__":
    unittest.main()
