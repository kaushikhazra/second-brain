"""Unit tests for config.py."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import config


class TestNormaliseHost(unittest.TestCase):
    def test_bare_ip_gets_scheme_and_default_port(self):
        self.assertEqual(config.normalise_host("192.168.1.5"), "http://192.168.1.5:11434")

    def test_hostname_with_port_is_kept(self):
        self.assertEqual(config.normalise_host("box.local:9999"), "http://box.local:9999")

    def test_full_url_path_is_discarded(self):
        # The legacy /v1 suffix must not survive; the native API lives at /api/chat.
        self.assertEqual(
            config.normalise_host("http://localhost:11434/v1"), "http://localhost:11434"
        )

    def test_https_is_preserved(self):
        self.assertEqual(config.normalise_host("https://ollama.example.com"), "https://ollama.example.com:11434")

    def test_surrounding_whitespace_is_ignored(self):
        self.assertEqual(config.normalise_host("  10.0.0.4  "), "http://10.0.0.4:11434")

    def test_empty_is_rejected(self):
        with self.assertRaises(config.ConfigError):
            config.normalise_host("   ")

    def test_unsupported_scheme_is_rejected(self):
        with self.assertRaises(config.ConfigError):
            config.normalise_host("ftp://box:11434")


class TestConfigFile(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.path = Path(self.tempdir.name, "config.json")

    def test_absent_file_yields_defaults(self):
        self.assertEqual(config.load_config(self.path), config.default_config())

    def test_round_trip(self):
        interpreter = Path(self.tempdir.name, "py.exe")
        config.save_config(
            {"python": str(interpreter), "ollama_host": "http://box:11434", "model": "m:1"},
            self.path,
        )

        loaded = config.load_config(self.path)

        self.assertEqual(loaded["ollama_host"], "http://box:11434")
        self.assertEqual(loaded["model"], "m:1")
        # Compared as a Path: the value round-trips through relative storage and
        # comes back with native separators, so string equality is the wrong test.
        self.assertEqual(Path(loaded["python"]), interpreter)

    def test_partial_file_falls_back_per_key(self):
        self.path.write_text(json.dumps({"model": "only:1"}), encoding="utf-8")

        loaded = config.load_config(self.path)

        self.assertEqual(loaded["model"], "only:1")
        self.assertEqual(loaded["ollama_host"], config.DEFAULT_HOST)
        self.assertIsNone(loaded["python"])

    def test_corrupt_file_is_treated_as_absent_rather_than_fatal(self):
        self.path.write_text("{not json", encoding="utf-8")

        self.assertEqual(config.load_config(self.path), config.default_config())

    def test_bom_prefixed_file_is_still_read(self):
        # Windows editors and `Out-File -Encoding utf8` write a BOM; reading as
        # plain utf-8 leaves it in the string and silently loses the whole file.
        self.path.write_text(json.dumps({"model": "bom:1"}), encoding="utf-8-sig")

        self.assertEqual(config.load_config(self.path)["model"], "bom:1")

    def test_unknown_keys_are_dropped_on_save(self):
        config.save_config({"model": "m:1", "junk": "x"}, self.path)

        self.assertEqual(set(json.loads(self.path.read_text())), set(config.default_config()))

    def test_paths_are_stored_relative_and_returned_absolute(self):
        interpreter = Path(self.tempdir.name, "sub", "python.exe")
        config.save_config({"python": str(interpreter), "model": "m:1"}, self.path)

        on_disk = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["python"], "sub/python.exe")
        self.assertFalse(Path(on_disk["python"]).is_absolute())

        loaded = config.load_config(self.path)
        self.assertTrue(Path(loaded["python"]).is_absolute())
        self.assertEqual(Path(loaded["python"]), interpreter)

    def test_relative_path_survives_the_config_moving(self):
        # The point of relative storage: copy the folder, keep working.
        config.save_config({"python": str(Path(self.tempdir.name, "v", "python.exe"))}, self.path)
        moved_dir = Path(self.tempdir.name, "elsewhere")
        moved_dir.mkdir()
        moved = moved_dir / "config.json"
        moved.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")

        self.assertEqual(
            Path(config.load_config(moved)["python"]), moved_dir / "v" / "python.exe"
        )

    def test_paths_above_the_config_use_parent_segments(self):
        interpreter = Path(self.tempdir.name).parent / "outside" / "python.exe"
        config.save_config({"python": str(interpreter)}, self.path)

        stored = json.loads(self.path.read_text(encoding="utf-8"))["python"]
        self.assertTrue(stored.startswith("../"))
        self.assertEqual(Path(config.load_config(self.path)["python"]), interpreter)

    def test_absolute_stored_path_is_passed_through(self):
        # A hand-edited config with an absolute path must keep working.
        absolute = str(Path(self.tempdir.name, "python.exe"))
        self.path.write_text(json.dumps({"python": absolute}), encoding="utf-8")

        self.assertEqual(config.load_config(self.path)["python"], absolute)

    def test_unset_path_stays_none(self):
        config.save_config({"python": None, "model": "m:1"}, self.path)

        self.assertIsNone(json.loads(self.path.read_text(encoding="utf-8"))["python"])
        self.assertIsNone(config.load_config(self.path)["python"])

    def test_cross_drive_path_falls_back_to_absolute(self):
        # os.path.relpath raises across Windows drives; there is no relative form.
        with mock.patch.object(config.os.path, "relpath", side_effect=ValueError):
            self.assertEqual(config.to_stored_path("Z:/py/python.exe"), "Z:/py/python.exe")

    def test_is_configured_requires_a_model(self):
        self.assertFalse(config.is_configured(config.default_config()))
        self.assertTrue(config.is_configured({"model": "m:1"}))

    def test_config_lives_beside_skill_md(self):
        self.assertTrue((config.skill_directory() / "SKILL.md").is_file())
        self.assertEqual(config.config_path().parent, config.skill_directory())


class TestDependencies(unittest.TestCase):
    def test_absent_module_is_reported_by_requirement_name(self):
        with mock.patch.object(config.importlib.util, "find_spec", return_value=None):
            self.assertEqual(
                config.missing_dependencies(), [req for _, req in config.REQUIRED_PACKAGES]
            )

    def test_present_modules_report_nothing(self):
        with mock.patch.object(config.importlib.util, "find_spec", return_value=object()):
            self.assertEqual(config.missing_dependencies(), [])


class TestInterpreter(unittest.TestCase):
    def test_unset_interpreter_means_stay_put(self):
        self.assertTrue(config.interpreter_matches(None))
        self.assertIsNone(config.resolve_interpreter(None))

    def test_current_interpreter_does_not_trigger_a_reexec(self):
        self.assertTrue(config.interpreter_matches(sys.executable))
        self.assertIsNone(config.resolve_interpreter(sys.executable))

    def test_missing_interpreter_is_rejected(self):
        with self.assertRaises(config.ConfigError):
            config.resolve_interpreter(str(Path(tempfile.gettempdir(), "no-such-python.exe")))

    def test_existing_other_interpreter_is_returned(self):
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as handle:
            other = handle.name
        self.addCleanup(os.unlink, other)

        self.assertEqual(config.resolve_interpreter(other), other)

    def test_reexec_guard_reads_the_environment(self):
        with mock.patch.dict(os.environ, {"LOCAL_AGENT_REEXEC": "1"}):
            self.assertTrue(config.reexec_guard_active())
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(config.reexec_guard_active())
