"""PDF setup checks without real downloads or software installation. MIT."""

import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tarfile
import unittest
from unittest.mock import patch
import uuid


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "skills" / "revision-comparison" / "scripts" / "setup_pdf.py"
SPEC = importlib.util.spec_from_file_location("pdf_setup", SOURCE)
PDF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PDF)
RUN = ROOT / ".scratch" / "pdf-tests" / uuid.uuid4().hex


class PdfSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        RUN.mkdir(parents=True)
        print("PDF test artifacts retained at {}".format(RUN), flush=True)

    def setUp(self):
        self.area = RUN / self._testMethodName
        self.area.mkdir()

    def archive(self, entries):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode="w:xz") as archive:
            for name, contents, link in entries:
                member = tarfile.TarInfo(name)
                if link:
                    member.type = tarfile.SYMTYPE
                    member.linkname = link
                    archive.addfile(member)
                else:
                    member.size = len(contents)
                    member.mode = 0o755
                    archive.addfile(member, io.BytesIO(contents))
        return data.getvalue()

    def test_check_requires_opt_in_to_install(self):
        with patch.object(PDF, "find_engine", return_value=None), \
                patch.object(PDF, "install_tinytex") as install:
            self.assertEqual(PDF.main(["--check"]), 1)
        install.assert_not_called()

    def test_existing_complete_latex_is_reused(self):
        engine = self.area / "existing latex" / "pdflatex"
        with patch.object(PDF, "find_engine", return_value=engine), \
                patch.object(PDF, "missing_packages", return_value=[]), \
                patch.object(PDF, "check_build", return_value=self.area / "check.pdf") as build, \
                patch.object(PDF, "install_tinytex") as install, \
                patch.object(PDF, "install_packages") as packages:
            self.assertEqual(PDF.main(["--install"]), 0)
        install.assert_not_called()
        packages.assert_not_called()
        build.assert_called_once_with(engine)

    def test_missing_packages_are_added_and_rechecked(self):
        engine = self.area / "pdflatex"
        with patch.object(PDF, "find_engine", return_value=engine), \
                patch.object(PDF, "missing_packages", side_effect=[["tcolorbox"], []]), \
                patch.object(PDF, "check_build", return_value=self.area / "check.pdf"), \
                patch.object(PDF, "install_tinytex") as install, \
                patch.object(PDF, "install_packages") as packages:
            self.assertEqual(PDF.main(["--install"]), 0)
        install.assert_not_called()
        packages.assert_called_once_with(engine, ["tcolorbox"])

    def test_existing_toolchain_directory_is_never_replaced(self):
        target = self.area / "existing TinyTeX"
        target.mkdir()
        marker = target / "marker"
        marker.write_bytes(b"keep existing LaTeX")
        with patch.object(PDF, "managed_root", return_value=target), patch.object(PDF, "urlopen") as download:
            with self.assertRaises(PDF.SetupError):
                PDF.install_tinytex()
        download.assert_not_called()
        self.assertEqual(marker.read_bytes(), b"keep existing LaTeX")

    def test_portable_install_uses_a_new_directory_with_spaces(self):
        target = self.area / "home with spaces" / "TinyTeX"
        scratch = self.area / "download"
        scratch.mkdir()
        bundle = self.archive([(".TinyTeX/bin/x86_64-linux/pdflatex", b"test executable", None)])
        engine = target / "bin" / "x86_64-linux" / "pdflatex"
        with patch.object(PDF, "managed_root", return_value=target), \
                patch.object(PDF, "bundle_name", return_value="TinyTeX-1-linux-x86_64.tar.xz"), \
                patch.object(PDF.platform, "system", return_value="Linux"), \
                patch.object(PDF.shutil, "which", return_value="/usr/bin/perl"), \
                patch.object(PDF.tempfile, "mkdtemp", return_value=str(scratch)), \
                patch.object(PDF, "urlopen", return_value=io.BytesIO(bundle)), \
                patch.object(PDF, "find_engine", return_value=engine):
            self.assertEqual(PDF.install_tinytex(), engine)
        self.assertEqual(engine.read_bytes(), b"test executable")
        self.assertTrue((scratch / ".TinyTeX" / "bin" / "x86_64-linux" / "pdflatex").is_file())

    def test_archive_paths_cannot_escape_the_setup_directory(self):
        marker = self.area / "marker"
        marker.write_bytes(b"preserved")
        for index, entry in enumerate([
            ("../marker", b"overwrite", None),
            (str(marker), b"overwrite", None),
            (".TinyTeX/link", b"", "../../marker"),
        ]):
            with self.subTest(entry=entry):
                archive = self.area / "bad-{}.tar.xz".format(index)
                archive.write_bytes(self.archive([entry]))
                destination = self.area / "extract-{}".format(index)
                destination.mkdir()
                with self.assertRaises(PDF.SetupError):
                    PDF.extract_bundle(archive, destination)
                self.assertEqual(marker.read_bytes(), b"preserved")

    @unittest.skipIf(os.name == "nt", "Creating symlinks may require Windows Developer Mode")
    def test_internal_executable_links_are_preserved(self):
        archive = self.area / "valid.tar.xz"
        archive.write_bytes(self.archive([
            (".TinyTeX/bin/pdftex", b"executable", None),
            (".TinyTeX/bin/pdflatex", b"", "pdftex"),
        ]))
        destination = self.area / "extract"
        destination.mkdir()
        PDF.extract_bundle(archive, destination)
        linked = destination / ".TinyTeX" / "bin" / "pdflatex"
        self.assertTrue(linked.is_symlink())
        self.assertEqual(linked.read_bytes(), b"executable")

    def test_read_only_texlive_uses_user_packages_without_sudo(self):
        engine = self.area / "system" / "pdflatex"
        root = self.area / "system tree"
        home = self.area / "user tree"
        database = root / "tlpkg" / "texlive.tlpdb"
        database.parent.mkdir(parents=True)
        database.write_text("test database")
        commands = []

        def command(args, **kwargs):
            commands.append(args)
            value = str(root) if args[-1] == "-var-value=TEXMFROOT" else str(home)
            return subprocess.CompletedProcess(args, 0, stdout=value)

        with patch.object(PDF, "companion", side_effect=lambda _, name: str(self.area / name)), \
                patch.object(PDF.os, "access", return_value=False), patch.object(PDF, "run", side_effect=command):
            PDF.install_packages(engine, ["tcolorbox"])
        self.assertIn([str(self.area / "tlmgr"), "--usermode", "init-usertree"], commands)
        self.assertEqual(commands[-1], [str(self.area / "tlmgr"), "--usermode", "install", "tcolorbox"])

    def test_miktex_install_and_check_are_separate(self):
        engine = self.area / "pdflatex.exe"
        manager = self.area / "miktex.exe"
        manager.write_bytes(b"test package manager")
        (self.area / "kpsewhich.exe").write_bytes(b"test file lookup")
        with patch.object(PDF.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout="found")) as lookup:
            self.assertEqual(PDF.missing_packages(engine), [])
        for call in lookup.call_args_list:
            self.assertIn("--miktex-disable-installer", call.args[0])
            self.assertIn("--miktex-disable-maintenance", call.args[0])
        with patch.object(PDF, "run") as command:
            PDF.install_packages(engine, ["tcolorbox", "lm"])
        command.assert_called_once_with([str(manager), "packages", "install", "tcolorbox", "lm"])
        build = self.area / "build"
        build.mkdir()

        def compile_check(args, **kwargs):
            self.assertIn("--disable-installer", args)
            self.assertIn("--disable-write18", args)
            (Path(kwargs["cwd"]) / "check.pdf").write_bytes(b"%PDF-test fixture")

        with patch.object(PDF.tempfile, "mkdtemp", return_value=str(build)), \
                patch.object(PDF, "run", side_effect=compile_check):
            self.assertEqual(PDF.check_build(engine), build / "check.pdf")


if __name__ == "__main__":
    unittest.main()
