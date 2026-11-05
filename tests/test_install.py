"""Installer checks; all scratch files are retained. MIT; see ../LICENSE."""

import os
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid


ROOT = Path(__file__).resolve().parent.parent
INSTALLER = ROOT / "scripts" / "install.py"
SOURCE = ROOT / "skills" / "revision-comparison"
RUN = ROOT / ".scratch" / "install-tests" / uuid.uuid4().hex
SPEC = importlib.util.spec_from_file_location("skill_installer", INSTALLER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        RUN.mkdir(parents=True)
        print("Installer test artifacts retained at {}".format(RUN), flush=True)

    def setUp(self):
        self.area = RUN / self._testMethodName
        self.area.mkdir()
        self.env = dict(os.environ)
        self.env["HOME"] = str(self.area / "isolated home")
        self.env["CODEX_HOME"] = str(self.area / "isolated codex home")
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"

    def install(self, *arguments):
        return subprocess.run(
            [sys.executable, "-B", str(INSTALLER), *map(str, arguments)],
            cwd=str(ROOT), env=self.env, capture_output=True, text=True,
        )

    def assert_complete(self, target):
        originals = {p.relative_to(SOURCE) for p in SOURCE.rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
        installed = {p.relative_to(target) for p in target.rglob("*") if p.is_file()}
        self.assertEqual(originals, installed)
        for relative in originals:
            self.assertEqual((SOURCE / relative).read_bytes(), (target / relative).read_bytes())
        self.assertIn(Path("references/rendering.md"), installed)
        self.assertIn(Path("assets/annotations.tex"), installed)

    def test_new_complete_custom_install(self):
        nested = SOURCE / "installer-must-not-create-this"
        result = self.install("--dest", nested)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(os.path.lexists(nested))
        target = self.area / "custom destination" / "revision-comparison"
        result = self.install("--dest", target)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(target), result.stdout)
        self.assert_complete(target)

    def test_existing_install_preserved(self):
        target = self.area / "existing"
        target.mkdir()
        marker = target / "marker.txt"
        marker.write_bytes(b"preserve this installation\n")
        result = self.install("--dest", target)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("preserved", result.stderr)
        self.assertEqual(marker.read_bytes(), b"preserve this installation\n")
        self.assertEqual(list(target.iterdir()), [marker])

    def test_dangling_symlink_preserved(self):
        target = self.area / "existing link"
        missing = self.area / "missing destination"
        target.symlink_to(missing, target_is_directory=True)
        result = self.install("--dest", target)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(target.is_symlink())
        self.assertEqual(os.readlink(target), str(missing))
        self.assertFalse(missing.exists())

    def test_host_destinations_and_project_spaces(self):
        project = self.area / "project with spaces"
        project.mkdir()
        user_cases = (
            ("codex", Path(self.env["HOME"]) / ".agents" / "skills" / "revision-comparison"),
            ("claude-code", Path(self.env["HOME"]) / ".claude" / "skills" / "revision-comparison"),
        )
        for agent, target in user_cases:
            with self.subTest(agent=agent, scope="user"):
                result = self.install("--agent", agent)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_complete(target)
        self.assertFalse(Path(self.env["CODEX_HOME"]).exists())
        for agent, host in (("codex", ".agents"), ("claude-code", ".claude")):
            with self.subTest(agent=agent, scope="project"):
                result = self.install("--agent", agent, "--scope", "project", "--project", project)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_complete(project / host / "skills" / "revision-comparison")
        result = self.install("--scope", "project")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires --project", result.stderr)

    def test_pdf_setup_failure_and_retry_preserve_the_installed_skill(self):
        target = self.area / "new skill"
        with patch.object(MODULE, "setup_pdf", return_value=1):
            self.assertEqual(MODULE.main(["--dest", str(target), "--with-pdf"]), 1)
        self.assert_complete(target)
        marker = target / "user-note.md"
        marker.write_bytes(b"preserve user changes")
        with patch.object(MODULE, "setup_pdf", return_value=0) as setup:
            self.assertEqual(MODULE.main(["--dest", str(target), "--with-pdf"]), 0)
        setup.assert_called_once_with()
        self.assertEqual(marker.read_bytes(), b"preserve user changes")

    def test_pdf_setup_rejects_source_and_unrelated_existing_targets(self):
        unrelated = self.area / "unrelated"
        unrelated.mkdir()
        marker = unrelated / "SKILL.md"
        marker.write_text("---\nname: unrelated-skill\n---\n", encoding="utf-8")
        with patch.object(MODULE, "setup_pdf") as setup:
            self.assertEqual(MODULE.main(["--dest", str(SOURCE), "--with-pdf"]), 1)
            self.assertEqual(MODULE.main(["--dest", str(unrelated), "--with-pdf"]), 1)
        setup.assert_not_called()
        self.assertEqual(marker.read_text(encoding="utf-8"), "---\nname: unrelated-skill\n---\n")


if __name__ == "__main__":
    unittest.main()
