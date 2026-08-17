import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


TARGET = Path(__file__).resolve().parents[1] / "scripts" / "generate_image.py"
SPEC = importlib.util.spec_from_file_location("relay_generate_image", TARGET)
CLIENT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = CLIENT
SPEC.loader.exec_module(CLIENT)


class RelayOutputDirectoryTests(unittest.TestCase):
    def test_project_defaults_use_separate_project_local_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            project = home / "work" / "demo"
            nested = project / "src"
            nested.mkdir(parents=True)
            (project / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            callai = CLIENT.default_output_dir(
                CLIENT.resolve_provider("callai"),
                cwd=nested,
                platform_name="darwin",
                home=home,
            )
            onepk = CLIENT.default_output_dir(
                CLIENT.resolve_provider("1pkapi"),
                cwd=nested,
                platform_name="darwin",
                home=home,
            )
            expected_root = project / ".generated_images" / "third-party" / "relay"
            self.assertEqual(callai, (expected_root / "callai").resolve())
            self.assertEqual(onepk, (expected_root / "1pkapi").resolve())
            self.assertNotEqual(callai, onepk)
            self.assertNotIn("outputs", callai.parts)

    def test_no_project_uses_downloads_on_macos(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            home.mkdir()
            provider = CLIENT.resolve_provider("callai")
            self.assertEqual(
                CLIENT.default_output_dir(
                    provider,
                    cwd=home,
                    platform_name="darwin",
                    home=home,
                ),
                (home / "Downloads" / "generated_images" / "third-party" / "relay" / "callai").resolve(),
            )

    def test_no_project_uses_desktop_on_windows(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            home.mkdir()
            provider = CLIENT.resolve_provider("callai")
            self.assertEqual(
                CLIENT.default_output_dir(
                    provider,
                    cwd=home,
                    platform_name="win32",
                    home=home,
                ),
                (home / "Desktop" / "generated_images" / "third-party" / "relay" / "callai").resolve(),
            )

    def test_explicit_output_dir_remains_available(self):
        with tempfile.TemporaryDirectory() as temporary:
            selected = Path(temporary) / "project-assets"
            args = CLIENT._parser().parse_args(["--output-dir", str(selected)])
            self.assertEqual(args.output_dir, selected)


if __name__ == "__main__":
    unittest.main()
