import importlib.util
import base64
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
    def test_project_defaults_use_shared_project_local_layout(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "work" / "demo"
            nested = project / "src"
            nested.mkdir(parents=True)
            (project / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            layout = CLIENT.resolve_layout(cwd=nested, task_namespace="relay")
            self.assertEqual(
                layout.images_dir,
                (project / "generated_images" / "images" / layout.date_label).resolve(),
            )
            self.assertEqual(
                layout.prompts_dir,
                (project / "generated_images" / "prompts" / layout.date_label).resolve(),
            )

    def test_no_project_requires_explicit_output_dir(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(CLIENT.ImageOutputLayoutError):
                CLIENT.resolve_layout(cwd=Path(temporary), task_namespace="relay")

    def test_saved_image_has_matching_markdown_prompt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            (root / ".git").mkdir(parents=True)
            layout = CLIENT.resolve_layout(cwd=root, task_namespace="relay")
            image_data = base64.b64encode(b"\x89PNG\r\n\x1a\nmock").decode("ascii")
            files = CLIENT._save_images(
                {"data": [{"b64_json": image_data}]},
                "test-key",
                layout.images_dir,
                object(),
                CLIENT.resolve_provider("callai"),
                layout,
                "海报草案",
                {"provider": "CallAI", "model": "gpt-image-2"},
            )
            image = Path(files[0])
            self.assertTrue(image.is_file())
            prompt = layout.prompts_dir / f"{image.stem}.md"
            self.assertIn("海报草案", prompt.read_text(encoding="utf-8"))

    def test_explicit_output_dir_remains_available(self):
        with tempfile.TemporaryDirectory() as temporary:
            selected = Path(temporary) / "project-assets"
            args = CLIENT._parser().parse_args(["--output-dir", str(selected)])
            self.assertEqual(args.output_dir, selected)


if __name__ == "__main__":
    unittest.main()
