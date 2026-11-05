"""PDF setup checks without real downloads or software installation. MIT."""

import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "skills" / "revision-comparison" / "scripts" / "setup_pdf.py"
SPEC = importlib.util.spec_from_file_location("pdf_setup", SOURCE)
PDF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PDF)
RENDER_PREVIEWS = PDF.render_previews
RUN = ROOT / ".scratch" / "pdf-tests" / uuid.uuid4().hex
MKDTEMP = tempfile.mkdtemp


class Clock:
    def __init__(self):
        self.now = 100.0

    def monotonic(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class PdfSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        RUN.mkdir(parents=True)
        print("PDF test artifacts retained at {}".format(RUN), flush=True)

    def setUp(self):
        self.area = RUN / self._testMethodName
        self.area.mkdir()
        self.addCleanup(patch.stopall)
        patch.object(PDF, "managed_root", return_value=self.area / "private TinyTeX").start()
        patch.object(PDF, "urlopen", side_effect=AssertionError("Tests must never access the network")).start()
        patch.object(PDF, "render_previews", return_value=([], "renderer-unavailable")).start()

        def task_scratch(*args, **kwargs):
            kwargs.setdefault("dir", str(self.area))
            return MKDTEMP(*args, **kwargs)

        patch.object(PDF.tempfile, "mkdtemp", side_effect=task_scratch).start()

    def engine(self, name="pdflatex", tree="system"):
        engine = self.area / tree / "bin" / name
        engine.parent.mkdir(parents=True, exist_ok=True)
        engine.write_bytes(b"#!/bin/sh\nexit 0\n")
        engine.chmod(0o755)
        return engine

    def source(self):
        source = self.area / "report.tex"
        source.write_text("\\documentclass{article}\n\\begin{document}Report\\end{document}\n")
        return source

    def state(self, source):
        return json.loads(source.with_name("." + source.stem + ".pdf-build.json").read_text())

    @staticmethod
    def version(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="Fixture TeX", stderr="")

    @staticmethod
    def successful_compile(engine, source, build, deadline, miktex=False):
        pdf = build / "comparison.pdf"
        pdf.write_bytes(b"%PDF-fixture report")
        return pdf, []

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
        with patch.object(PDF, "select_engine", side_effect=PDF.SetupError("No compiler")), \
                patch.object(PDF, "install_tinytex") as install:
            self.assertEqual(PDF.main(["--check"]), 1)
        install.assert_not_called()

    def test_existing_complete_latex_is_reused(self):
        engine = self.area / "existing latex" / "pdflatex"
        with patch.object(PDF, "select_engine", return_value=(engine, self.area / "check.pdf")) as select, \
                patch.object(PDF, "install_tinytex") as install, \
                patch.object(PDF, "install_packages") as packages:
            self.assertEqual(PDF.main(["--install"]), 0)
        install.assert_not_called()
        packages.assert_not_called()
        select.assert_called_once_with(None, False)

    def test_missing_system_packages_trigger_private_install_and_recheck(self):
        engine = self.area / "private TinyTeX" / "bin" / "pdflatex"
        with patch.object(PDF, "select_engine", side_effect=[PDF.SetupError("System packages missing"),
                          (engine, self.area / "check.pdf")]) as select, \
                patch.object(PDF, "engine_candidates", return_value=[engine]), \
                patch.object(PDF, "missing_packages", return_value=["tcolorbox"]), \
                patch.object(PDF, "install_tinytex", return_value=engine) as install, \
                patch.object(PDF, "install_packages") as packages:
            self.assertEqual(PDF.main(["--install"]), 0)
        install.assert_called_once_with()
        packages.assert_called_once_with(engine, ["tcolorbox"])
        self.assertEqual(select.call_args_list[-1].args, (None, False, [engine]))

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
                patch.object(PDF, "engine_candidates", return_value=[engine]):
            self.assertEqual(PDF.install_tinytex(), engine)
        self.assertEqual(engine.read_bytes(), b"test executable")
        self.assertTrue((scratch / ".TinyTeX" / "bin" / "x86_64-linux" / "pdflatex").is_file())
        self.assertEqual(json.loads((target / PDF.OWNER_FILE).read_text())["owner"], "revision-comparison")

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

    def test_package_installation_refuses_unowned_or_linked_trees(self):
        for case in ("unmarked", "wrong-owner", "external-engine", "linked-marker", "linked-root"):
            with self.subTest(case=case):
                base = self.area / case
                root = base / "TinyTeX"
                engine = root / "bin" / "pdflatex"
                engine.parent.mkdir(parents=True)
                engine.write_bytes(b"preserve compiler")
                marker = root / PDF.OWNER_FILE
                if case != "unmarked":
                    marker.write_text(json.dumps({"owner": "other" if case == "wrong-owner" else "revision-comparison"}))
                if case == "external-engine":
                    engine = base / "external-pdflatex"
                    engine.write_bytes(b"preserve external compiler")
                elif case == "linked-marker":
                    linked = root / "owner-link"
                    linked.symlink_to(marker)
                    marker = linked
                    with patch.object(PDF, "OWNER_FILE", "owner-link"):
                        self.assert_unowned_install_is_read_only(root, engine)
                    continue
                elif case == "linked-root":
                    linked = base / "root-link"
                    linked.symlink_to(root, target_is_directory=True)
                    root = linked
                    engine = linked / "bin" / "pdflatex"
                self.assert_unowned_install_is_read_only(root, engine)
                self.assertEqual(engine.read_bytes(), b"preserve external compiler" if case == "external-engine" else b"preserve compiler")

    def assert_unowned_install_is_read_only(self, root, engine):
        with patch.object(PDF, "managed_root", return_value=root), \
                patch.object(PDF, "run") as command, patch.object(PDF, "companion") as lookup:
            with self.assertRaisesRegex(PDF.SetupError, "read-only"):
                PDF.install_packages(engine, ["tcolorbox"])
        command.assert_not_called()
        lookup.assert_not_called()

    def test_marked_private_packages_use_only_the_private_manager(self):
        root = PDF.managed_root()
        engine = self.engine(tree="private TinyTeX")
        (root / PDF.OWNER_FILE).write_text(json.dumps({"owner": "revision-comparison", "schema": 1}))
        manager = engine.parent / "tlmgr"
        manager.write_bytes(b"fixture manager")
        (engine.parent / "kpsewhich").write_bytes(b"fixture lookup")
        before = dict(os.environ)
        with patch.object(PDF, "run", side_effect=lambda args, **kwargs:
                          subprocess.CompletedProcess(args, 0, stdout=str(root))) as command:
            PDF.install_packages(engine, ["tcolorbox", "lm"])
        self.assertEqual(command.call_args_list[0].args[0],
                         [str(engine.parent / "kpsewhich"), "-var-value=TEXMFROOT"])
        self.assertEqual(command.call_args_list[-1].args[0], [str(manager), "install", "tcolorbox", "lm"])
        self.assertEqual(command.call_count, 2)
        environment = PDF.tex_environment(engine)
        self.assertEqual(environment["TEXMFHOME"], str(root / "user" / "texmf"))
        self.assertEqual(environment["TEXMFCONFIG"], str(root / "user" / "config"))
        self.assertEqual(os.environ, before)

    def test_private_manager_cannot_redirect_installation_outside_owned_root(self):
        root = PDF.managed_root()
        engine = self.engine(tree="private TinyTeX")
        (root / PDF.OWNER_FILE).write_text(json.dumps({"owner": "revision-comparison"}))
        with patch.object(PDF, "companion", side_effect=lambda _, name: str(engine.parent / name)), \
                patch.object(PDF, "run", return_value=subprocess.CompletedProcess([], 0, stdout=str(self.area / "external"))) as command:
            with self.assertRaisesRegex(PDF.SetupError, "outside"):
                PDF.install_packages(engine, ["tcolorbox"])
        self.assertEqual(command.call_count, 1)

    def test_install_mode_preserves_unmarked_private_directory(self):
        root = PDF.managed_root()
        root.mkdir()
        marker = root / "keep.txt"
        marker.write_bytes(b"user files")
        engine = self.area / "outside" / "pdflatex"
        with patch.object(PDF, "select_engine", side_effect=PDF.SetupError("No usable compiler")), \
                patch.object(PDF, "engine_candidates", return_value=[engine]), \
                patch.object(PDF, "install_tinytex") as install, \
                patch.object(PDF, "install_packages") as packages:
            self.assertEqual(PDF.main(["--install"]), 1)
        install.assert_not_called()
        packages.assert_not_called()
        self.assertEqual(marker.read_bytes(), b"user files")

    def test_miktex_install_and_check_are_separate(self):
        engine = self.area / "pdflatex.exe"
        manager = self.area / "miktex.exe"
        manager.write_bytes(b"test package manager")
        (self.area / "kpsewhich.exe").write_bytes(b"test file lookup")
        with patch.object(PDF, "run", return_value=subprocess.CompletedProcess([], 0, stdout="found")) as lookup:
            self.assertEqual(PDF.missing_packages(engine), [])
        for call in lookup.call_args_list:
            self.assertIn("--miktex-disable-installer", call.args[0])
            self.assertIn("--miktex-disable-maintenance", call.args[0])
        with patch.object(PDF, "run") as command:
            with self.assertRaisesRegex(PDF.SetupError, "read-only"):
                PDF.install_packages(engine, ["tcolorbox", "lm"])
        command.assert_not_called()
        build = self.area / "build"
        build.mkdir()

        def compile_check(args, **kwargs):
            self.assertIn("--disable-installer", args)
            self.assertIn("--disable-write18", args)
            (Path(kwargs["cwd"]) / "check.pdf").write_bytes(b"%PDF-test fixture")

        with patch.object(PDF.tempfile, "mkdtemp", return_value=str(build)), \
                patch.object(PDF, "run", side_effect=compile_check):
            self.assertEqual(PDF.check_build(engine), build / "check.pdf")

    def test_miktex_shim_version_disables_installation_in_all_preflight_commands(self):
        engine = self.engine()
        (engine.parent / "kpsewhich").write_bytes(b"fixture lookup")
        self.assertFalse(PDF.is_miktex(engine), "the shim must have no adjacent MiKTeX manager")
        commands = []

        def command(args, **kwargs):
            commands.append(args)
            if "--version" in args:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="MiKTeX-pdfTeX fixture")
            if args[0] == str(engine.parent / "kpsewhich"):
                self.assertIn("--miktex-disable-installer", args)
                self.assertIn("--miktex-disable-maintenance", args)
                return subprocess.CompletedProcess(args, 0, stdout="fixture package path", stderr="")
            self.assertIn("--disable-installer", args)
            self.assertIn("--disable-write18", args)
            self.assertIn("--miktex-disable-maintenance", args)
            (Path(kwargs["cwd"]) / "check.pdf").write_bytes(b"%PDF-MiKTeX shim fixture")
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        with patch.object(PDF, "run", side_effect=command):
            selected, pdf = PDF.select_engine(candidates=[engine])
        self.assertEqual(selected, engine)
        self.assertTrue(pdf.is_file())
        lookups = [args for args in commands if args[0] == str(engine.parent / "kpsewhich")]
        self.assertEqual(len(lookups), sum(len(files) for files in PDF.PACKAGES.values()))
        self.assertEqual(sum("check.tex" in args for args in commands), 1)

    def test_path_installations_are_discovered_deduplicated_and_unicode_ordered(self):
        first = [self.engine(name, "TeX One") for name in PDF.ENGINES]
        second = [self.engine(name, "TeX Two") for name in PDF.ENGINES]
        alias = self.area / "same installation"
        alias.symlink_to(first[0].parent, target_is_directory=True)
        directories = {str(first[0].parent), str(second[0].parent), str(alias)}
        real_which = PDF.shutil.which

        def local_which(name, path=None):
            if path in directories or (path is None and str(name) == str(second[2])):
                return real_which(name, path=path)
            return None

        with patch.object(PDF.os, "get_exec_path", return_value=[str(first[0].parent), str(alias),
                          str(second[0].parent), str(first[0].parent)]), \
                patch.object(PDF.Path, "home", return_value=self.area / "fixture home"), \
                patch.object(PDF.shutil, "which", side_effect=local_which):
            ordinary = PDF.engine_candidates()
            unicode = PDF.engine_candidates(unicode=True)
            preferred = PDF.engine_candidates(preferred=second[2], unicode=True)
        self.assertEqual(ordinary, [first[0], second[0], first[1], second[1], first[2], second[2]])
        self.assertEqual(unicode, [first[1], second[1], first[2], second[2], first[0], second[0]])
        self.assertEqual(preferred[0], second[2])
        self.assertEqual(len(preferred), 6)
        self.assertEqual(set(preferred), set(ordinary))

    def test_engine_alias_names_are_preserved_when_the_target_is_shared(self):
        engine = self.engine("pdftex")
        alias = engine.with_name("pdflatex")
        alias.symlink_to(engine)
        real_which = PDF.shutil.which
        with patch.object(PDF.os, "get_exec_path", return_value=[str(engine.parent)]), \
                patch.object(PDF.Path, "home", return_value=self.area / "fixture home"), \
                patch.object(PDF.shutil, "which", side_effect=lambda name, path=None:
                             real_which(name, path=path) if path == str(engine.parent) else None):
            self.assertEqual(PDF.engine_candidates(), [alias])

    def test_private_discovery_never_includes_path_toolchains(self):
        private = PDF.managed_root() / "bin" / "platform" / "pdflatex"
        private.parent.mkdir(parents=True)
        private.write_bytes(b"#!/bin/sh\nexit 0\n")
        private.chmod(0o755)
        external = self.engine(tree="unrelated PATH toolchain")
        real_which = PDF.shutil.which
        with patch.object(PDF.os, "get_exec_path", return_value=[str(external.parent)]) as paths, \
                patch.object(PDF.shutil, "which", side_effect=real_which):
            candidates = PDF.engine_candidates(private_only=True)
        paths.assert_not_called()
        self.assertEqual(candidates, [private])

    def test_first_candidate_failure_falls_back_to_second(self):
        engines = [self.engine(tree="first"), self.engine("xelatex", "second")]
        checked = []

        def build(engine, deadline, directory, miktex=False):
            checked.append(engine)
            if engine == engines[0]:
                raise PDF.SetupError("broken format")
            return directory / "check.pdf"

        with patch.object(PDF, "engine_candidates", return_value=engines), \
                patch.object(PDF, "engine_version", return_value=False), \
                patch.object(PDF, "missing_packages", return_value=[]), \
                patch.object(PDF, "check_build", side_effect=build):
            selected, pdf = PDF.select_engine(unicode=True)
        self.assertEqual(selected, engines[1])
        self.assertEqual(checked, engines)
        self.assertEqual(pdf.name, "check.pdf")

    def test_candidate_probe_budget_includes_package_lookup_and_theme_build(self):
        clock = Clock()
        engines = [self.engine(tree="first"), self.engine(tree="second")]
        limits = []

        def version(engine, deadline):
            limits.append(deadline.limit(60))
            if engine == engines[0]:
                clock.advance(1)
            return False

        def packages(engine, deadline, miktex=False):
            limits.append(deadline.limit(60))
            if engine == engines[0]:
                clock.advance(13)
            return []

        def build(engine, deadline, directory, miktex=False):
            limits.append(deadline.limit(60))
            if engine == engines[0]:
                clock.advance(1)
                raise PDF.CommandTimeout("theme probe timeout")
            return directory / "check.pdf"

        with patch.object(PDF.time, "monotonic", side_effect=clock.monotonic), \
                patch.object(PDF, "engine_version", side_effect=version), \
                patch.object(PDF, "missing_packages", side_effect=packages), \
                patch.object(PDF, "check_build", side_effect=build):
            selected, _ = PDF.select_engine(candidates=engines)
        self.assertEqual(selected, engines[1])
        self.assertEqual(limits, [15, 14, 1, 15, 15, 15])

    def test_preflight_tries_at_most_three_candidates(self):
        engines = [self.engine(tree="toolchain-{}".format(n)) for n in range(5)]
        with patch.object(PDF, "engine_version", return_value=False), \
                patch.object(PDF, "missing_packages", return_value=[]) as packages, \
                patch.object(PDF, "check_build", side_effect=PDF.SetupError("bad format")) as build:
            with self.assertRaisesRegex(PDF.SetupError, "No usable"):
                PDF.select_engine(candidates=engines)
        self.assertEqual([call.args[0] for call in packages.call_args_list], engines[:3])
        self.assertEqual([call.args[0] for call in build.call_args_list], engines[:3])

    def test_missing_shared_packages_skip_sibling_engine_without_using_a_probe(self):
        engines = [self.engine(tree="first"), self.engine("xelatex", "first"), self.engine(tree="second")]
        with patch.object(PDF, "engine_version", return_value=False), \
                patch.object(PDF, "missing_packages", side_effect=[["tcolorbox"], []]) as packages, \
                patch.object(PDF, "check_build", return_value=self.area / "check.pdf") as build:
            selected, _ = PDF.select_engine(candidates=engines)
        self.assertEqual(selected, engines[2])
        self.assertEqual([call.args[0] for call in packages.call_args_list], [engines[0], engines[2]])
        self.assertEqual(build.call_args.args[0], engines[2])

    def test_package_probe_timeout_propagates_without_checking_more_files(self):
        engine = self.engine()
        with patch.object(PDF, "kpsewhich_command", return_value=[str(engine), "lookup"]), \
                patch.object(PDF, "run", side_effect=PDF.CommandTimeout("lookup stalled")) as command:
            with self.assertRaises(PDF.CommandTimeout):
                PDF.missing_packages(engine, PDF.Deadline(15))
        self.assertEqual(command.call_count, 1)

    def test_deadline_children_share_the_parent_remaining_budget(self):
        clock = Clock()
        with patch.object(PDF.time, "monotonic", side_effect=clock.monotonic):
            deadline = PDF.Deadline(120)
            self.assertEqual(deadline.limit(200), 120)
            clock.advance(110)
            child = deadline.child(15)
            self.assertEqual(child.limit(60), 10)
            clock.advance(7)
            self.assertEqual(child.limit(60), 3)
            self.assertEqual(deadline.limit(60), 3)
            clock.advance(3)
            with self.assertRaises(PDF.BudgetExpired):
                child.limit(1)
            with self.assertRaises(PDF.BudgetExpired):
                deadline.child(1)

    def test_expired_run_budget_never_launches_a_process(self):
        with patch.object(PDF.subprocess, "Popen") as launch:
            with self.assertRaises(PDF.BudgetExpired):
                PDF.run([sys.executable, "-B", "-c", "pass"], deadline=PDF.Deadline(end=0))
        launch.assert_not_called()

    @unittest.skipIf(os.name == "nt", "POSIX process-group cleanup test")
    def test_timeout_kills_its_child_process_and_preserves_unrelated_process(self):
        pids = self.area / "tree-pids.json"
        parent = self.area / "parent.py"
        parent.write_text(
            "import json, os, pathlib, subprocess, sys, time\n"
            "child = subprocess.Popen([sys.executable, '-B', '-c', 'import time; time.sleep(60)'])\n"
            "pathlib.Path(sys.argv[1]).write_text(json.dumps([os.getpid(), child.pid]))\n"
            "time.sleep(60)\n")
        unrelated = subprocess.Popen([sys.executable, "-B", "-c", "import time; time.sleep(60)"],
                                     cwd=str(self.area), start_new_session=True,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        started = time.monotonic()
        try:
            with self.assertRaises(PDF.CommandTimeout):
                PDF.run([sys.executable, "-B", str(parent), str(pids)], timeout=0.8,
                        capture_output=True, text=True, cwd=str(self.area), env=dict(os.environ))
            self.assertLess(time.monotonic() - started, 6)
            self.assertTrue(pids.is_file(), "controlled parent did not launch its child")
            parent_pid, child_pid = json.loads(pids.read_text())
            for pid in (parent_pid, child_pid):
                for _ in range(40):
                    result = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True,
                                            text=True, timeout=2, check=False)
                    status = result.stdout.strip()
                    if not status or status.startswith("Z"):
                        break
                    time.sleep(0.025)
                self.assertTrue(not status or status.startswith("Z"), "timed out process {} still runs: {}".format(pid, status))
            self.assertIsNone(unrelated.poll(), "timeout cleanup killed an unrelated process")
        finally:
            if pids.is_file():
                # Only the controlled process group created by this test is eligible for cleanup.
                parent_pid = json.loads(pids.read_text())[0]
                try:
                    os.killpg(parent_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            unrelated.terminate()
            unrelated.wait(timeout=5)

    def test_report_falls_back_to_a_working_candidate_and_preserves_existing_pdf(self):
        source = self.source()
        existing = source.with_suffix(".pdf")
        existing.write_bytes(b"existing user PDF")
        engines = [self.engine(tree="broken"), self.engine("xelatex", "working")]
        compiled = []

        def compile_candidate(engine, frozen, build, deadline, miktex=False):
            compiled.append(engine)
            self.assertEqual(frozen.read_bytes(), source.read_bytes())
            self.assertEqual(frozen.parent, build)
            if engine == engines[0]:
                raise PDF.BuildFailure("engine environment is broken", environment=True)
            return self.successful_compile(engine, frozen, build, deadline, miktex)

        with patch.object(PDF, "engine_candidates", return_value=engines), \
                patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "run", side_effect=self.version), \
                patch.object(PDF, "compile_document", side_effect=compile_candidate):
            result = PDF.compile_report(source)
        self.assertEqual(result["status"], "pdf-ready")
        self.assertEqual(result["compiler"], str(engines[1]))
        self.assertEqual(compiled, engines)
        self.assertEqual(Path(result["pdf"]), source.with_name("report-1.pdf"))
        self.assertTrue(Path(result["pdf"]).read_bytes().startswith(b"%PDF-"))
        self.assertEqual(existing.read_bytes(), b"existing user PDF")

    def test_report_compiler_crash_falls_back_instead_of_requesting_source_repair(self):
        source = self.source()
        engines = [self.engine(tree="crashing"), self.engine("xelatex", "working")]
        compiled = []

        def command(args, **kwargs):
            if "--version" in args:
                return self.version(args, **kwargs)
            engine = Path(args[0])
            compiled.append(engine)
            if engine == engines[0]:
                kwargs["stdout"].write("Compiler began reading the report, then crashed.\n")
                raise PDF.CommandFailed(args, -11)
            kwargs["stdout"].write("Compilation complete\n")
            output = next(arg.split("=", 1)[1] for arg in args if arg.startswith("-output-directory="))
            (Path(output) / "comparison.pdf").write_bytes(b"%PDF-after crash fixture")
            return subprocess.CompletedProcess(args, 0)

        with patch.object(PDF, "engine_candidates", return_value=engines), \
                patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "run", side_effect=command):
            result = PDF.compile_report(source)
        self.assertEqual(result["status"], "pdf-ready")
        self.assertEqual(result["compiler"], str(engines[1]))
        self.assertEqual(compiled, engines)
        self.assertEqual(result["attempt"], 1)

    def test_report_tries_at_most_three_candidates(self):
        source = self.source()
        engines = [self.engine(tree="toolchain-{}".format(n)) for n in range(5)]
        with patch.object(PDF, "engine_candidates", return_value=engines), \
                patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "run", side_effect=self.version) as version, \
                patch.object(PDF, "compile_document", side_effect=PDF.BuildFailure("bad environment", environment=True)) as compile_:
            result = PDF.compile_report(source)
        self.assertEqual(result["status"], "markdown-fallback")
        self.assertEqual([call.args[0] for call in compile_.call_args_list], engines[:3])
        self.assertEqual(version.call_count, 3)
        self.assertFalse(source.with_suffix(".pdf").exists())

    def test_report_source_error_does_not_blindly_retry_other_engines(self):
        source = self.source()
        engines = [self.engine(tree="first"), self.engine(tree="second")]
        with patch.object(PDF, "engine_candidates", return_value=engines), \
                patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "run", side_effect=self.version) as version, \
                patch.object(PDF, "compile_document", side_effect=PDF.BuildFailure("Undefined control sequence")) as compile_:
            result = PDF.compile_report(source)
        self.assertEqual(result["status"], "needs-repair")
        self.assertEqual(compile_.call_count, 1)
        self.assertEqual(version.call_count, 1)
        self.assertEqual(result["attempt"], 1)
        self.assertFalse(source.with_suffix(".pdf").exists())

    def test_report_allows_only_two_explicit_retry_calls(self):
        source = self.source()
        engine = self.engine()
        with patch.object(PDF, "engine_candidates", return_value=[engine]), \
                patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "run", side_effect=self.version), \
                patch.object(PDF, "compile_document", side_effect=PDF.BuildFailure("Undefined control sequence")) as compile_:
            results = [PDF.compile_report(source) for _ in range(5)]
        self.assertEqual([result["status"] for result in results],
                         ["needs-repair", "needs-repair", "markdown-fallback", "markdown-fallback", "markdown-fallback"])
        self.assertEqual([result["attempt"] for result in results], [1, 2, 3, 3, 3])
        self.assertEqual([result["repairs"] for result in results], [0, 1, 2, 2, 2])
        self.assertEqual(compile_.call_count, 3)
        self.assertEqual(self.state(source)["attempt"], 3)

    def test_external_input_change_recompiles_unchanged_wrapper_and_reuses_compiler(self):
        source = self.source()
        included = self.area / "content.tex"
        included.write_text("First revision")
        source.write_text("\\documentclass{article}\n\\begin{document}\\input{content.tex}\\end{document}\n")
        wrapper = source.read_bytes()
        engine = self.engine("xelatex")
        snapshots = []

        def compile_dependency(engine, frozen, build, deadline, miktex=False):
            snapshots.append(included.read_text())
            return self.successful_compile(engine, frozen, build, deadline, miktex)

        with patch.object(PDF, "engine_candidates", return_value=[engine]) as candidates, \
                patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "run", side_effect=self.version), \
                patch.object(PDF, "compile_document", side_effect=compile_dependency) as compile_:
            first = PDF.compile_report(source)
            included.write_text("Changed dependency")
            second = PDF.compile_report(source)
        self.assertEqual(source.read_bytes(), wrapper)
        self.assertEqual(snapshots, ["First revision", "Changed dependency"])
        self.assertEqual(compile_.call_count, 2)
        self.assertEqual((first["status"], second["status"]), ("pdf-ready", "pdf-ready"))
        self.assertNotEqual(first["pdf"], second["pdf"])
        self.assertEqual(candidates.call_args_list[-1].args[0], str(engine))
        self.assertEqual(second["attempt"], 2)

    def test_compile_cli_shares_120_second_budget_across_calls(self):
        source = self.source()
        engine = self.engine()
        clock = Clock()
        limits = []

        def version(args, **kwargs):
            self.assertGreaterEqual(kwargs["deadline"].limit(15), 5)
            clock.advance(5)
            return self.version(args, **kwargs)

        def timeout(engine, frozen, build, deadline, miktex=False):
            available = deadline.limit(PDF.COMPILE_SECONDS)
            limits.append(available)
            clock.advance(available)
            raise PDF.CommandTimeout("compile timed out")

        with patch.object(PDF.time, "monotonic", side_effect=clock.monotonic), \
                patch.object(PDF, "engine_candidates", return_value=[engine]), \
                patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "run", side_effect=version), \
                patch.object(PDF, "compile_document", side_effect=timeout) as compile_, \
                patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(PDF.main(["--compile", str(source)]), 1)
            first = self.state(source)
            self.assertEqual(first["remaining_seconds"], 55)
            self.assertEqual(PDF.main(["--compile", str(source)]), 1)
            second = self.state(source)
            self.assertEqual(second["remaining_seconds"], 0)
            self.assertEqual(PDF.main(["--compile", str(source)]), 1)
            final = self.state(source)
        self.assertEqual(limits, [60, 50])
        self.assertEqual(compile_.call_count, 2)
        self.assertEqual(final["attempt"], 2)
        self.assertEqual(final["status"], "markdown-fallback")
        self.assertIn("budget", final["reason"])
        self.assertEqual(clock.now - 100, 120)

    def test_render_previews_uses_the_compile_deadline_and_charges_its_budget(self):
        source = self.source()
        engine = self.engine()
        renderer = str(self.area / "fixture-pdftoppm")
        clock = Clock()
        compile_deadlines = []

        def compile_(engine, frozen, build, deadline, miktex=False):
            compile_deadlines.append(deadline)
            clock.advance(60)
            return self.successful_compile(engine, frozen, build, deadline, miktex)

        def command(args, **kwargs):
            if "--version" in args:
                clock.advance(5)
                return self.version(args, **kwargs)
            self.assertEqual(args[0], renderer)
            self.assertEqual(kwargs["timeout"], 30)
            self.assertIs(kwargs["deadline"], compile_deadlines[0])
            self.assertEqual(kwargs["deadline"].limit(120), 55)
            clock.advance(20)
            Path(args[-1] + "-1.png").write_bytes(b"fixture preview")
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        with patch.object(PDF.time, "monotonic", side_effect=clock.monotonic), \
                patch.object(PDF, "engine_candidates", return_value=[engine]), \
                patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "compile_document", side_effect=compile_), \
                patch.object(PDF, "run", side_effect=command), \
                patch.object(PDF.shutil, "which", return_value=renderer), \
                patch.object(PDF, "render_previews", wraps=RENDER_PREVIEWS):
            result = PDF.compile_report(source)
        self.assertEqual(result["status"], "pdf-ready")
        self.assertEqual(result["remaining_seconds"], 35)
        self.assertEqual(len(result["previews"]), 1)
        self.assertTrue(Path(result["previews"][0]).is_file())
        self.assertIn("rendered", result["preview_status"])

    def test_missing_preview_renderer_preserves_pdf_ready(self):
        source = self.source()
        engine = self.engine()
        with patch.object(PDF, "engine_candidates", return_value=[engine]), \
                patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "compile_document", side_effect=self.successful_compile), \
                patch.object(PDF, "run", side_effect=self.version) as command, \
                patch.object(PDF.shutil, "which", return_value=None), \
                patch.object(PDF, "render_previews", wraps=RENDER_PREVIEWS):
            result = PDF.compile_report(source)
        self.assertEqual(result["status"], "pdf-ready")
        self.assertTrue(PDF.is_pdf(Path(result["pdf"])))
        self.assertEqual(result["previews"], [])
        self.assertEqual(result["preview_status"], "renderer-unavailable")
        self.assertEqual(command.call_count, 1, "only the engine version command should run")

    def test_preview_timeout_preserves_pdf_and_uses_only_remaining_export_budget(self):
        source = self.source()
        engine = self.engine()
        renderer = str(self.area / "fixture-pdftoppm")
        clock = Clock()
        compile_deadlines = []

        def compile_(engine, frozen, build, deadline, miktex=False):
            compile_deadlines.append(deadline)
            clock.advance(100)  # More than one normal TeX pass can consume this time.
            return self.successful_compile(engine, frozen, build, deadline, miktex)

        def command(args, **kwargs):
            if "--version" in args:
                clock.advance(5)
                return self.version(args, **kwargs)
            self.assertEqual(args[0], renderer)
            self.assertEqual(kwargs["timeout"], 30)
            self.assertIs(kwargs["deadline"], compile_deadlines[0])
            remaining = kwargs["deadline"].limit(kwargs["timeout"])
            self.assertEqual(remaining, 15)
            clock.advance(remaining)
            Path(args[-1] + "-1.png").write_bytes(b"partial preview fixture")
            raise PDF.CommandTimeout("controlled renderer timeout")

        with patch.object(PDF.time, "monotonic", side_effect=clock.monotonic), \
                patch.object(PDF, "engine_candidates", return_value=[engine]), \
                patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "compile_document", side_effect=compile_), \
                patch.object(PDF, "run", side_effect=command), \
                patch.object(PDF.shutil, "which", return_value=renderer), \
                patch.object(PDF, "render_previews", wraps=RENDER_PREVIEWS):
            result = PDF.compile_report(source)
        self.assertEqual(result["status"], "pdf-ready")
        self.assertTrue(PDF.is_pdf(Path(result["pdf"])))
        self.assertIsNone(result["reason"])
        self.assertEqual(result["remaining_seconds"], 0)
        self.assertIn("controlled renderer timeout", result["preview_status"])
        self.assertEqual(len(result["previews"]), 1)
        self.assertEqual(clock.now - 100, 120)

    def test_compile_document_resolves_references_in_a_normal_second_pass(self):
        source = self.source()
        engine = self.engine()
        build = self.area / "build"
        build.mkdir()
        deadline = PDF.Deadline()
        outputs = ["LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.\n", "Compilation complete\n"]

        def command(args, **kwargs):
            kwargs["stdout"].write(outputs.pop(0))
            (build / "comparison.pdf").write_bytes(b"%PDF-reference fixture")

        with patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "run", side_effect=command) as command_:
            pdf, warnings = PDF.compile_document(engine, source, build, deadline)
        self.assertEqual(pdf, build / "comparison.pdf")
        self.assertEqual(warnings, [])
        self.assertEqual(command_.call_count, 2)
        for call in command_.call_args_list:
            self.assertIs(call.kwargs["deadline"], deadline)
            self.assertEqual(call.kwargs["timeout"], 60)
            self.assertIn("-no-shell-escape", call.args[0])

    def test_compile_document_stops_unsettled_references_after_three_passes(self):
        source = self.source()
        engine = self.engine()
        build = self.area / "build"
        build.mkdir()

        def command(args, **kwargs):
            kwargs["stdout"].write("LaTeX Warning: Label(s) may have changed.\n")
            (build / "comparison.pdf").write_bytes(b"%PDF-unsettled fixture")

        with patch.object(PDF, "is_miktex", return_value=False), \
                patch.object(PDF, "run", side_effect=command) as command_:
            with self.assertRaisesRegex(PDF.BuildFailure, "within 3 passes"):
                PDF.compile_document(engine, source, build, PDF.Deadline())
        self.assertEqual(command_.call_count, 3)

    def test_compile_document_distinguishes_source_errors_from_missing_dependencies(self):
        source = self.source()
        engine = self.engine()
        for index, (message, returncode, environment, dependency) in enumerate([
            ("! Undefined control sequence.\n", 1, False, False),
            ("! LaTeX Error: File `tcolorbox.sty' not found.\n", 1, True, True),
            ("Runtime crash after opening the input.\n", -11, True, False),
            ("Runtime crash after opening the input.\n", 139, True, False),
        ]):
            with self.subTest(message=message, returncode=returncode):
                build = self.area / "build-{}".format(index)
                build.mkdir()

                def command(args, **kwargs):
                    kwargs["stdout"].write(message)
                    raise PDF.CommandFailed(args, returncode)

                with patch.object(PDF, "is_miktex", return_value=False), \
                        patch.object(PDF, "run", side_effect=command) as command_:
                    with self.assertRaises(PDF.BuildFailure) as failure:
                        PDF.compile_document(engine, source, build, PDF.Deadline())
                self.assertEqual(failure.exception.environment, environment)
                self.assertEqual(failure.exception.shared_dependency, dependency)
                self.assertEqual(command_.call_count, 1)


if __name__ == "__main__":
    unittest.main()
