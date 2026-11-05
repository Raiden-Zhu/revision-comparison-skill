#!/usr/bin/env python3
"""Check or install LaTeX for the comparison theme. MIT; see repository LICENSE."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from urllib.request import urlopen


SKILL = Path(__file__).resolve().parent.parent
PACKAGES = {
    "latex": ("article.cls", "fontenc.sty"),
    "lm": ("lmodern.sty",),
    "xcolor": ("xcolor.sty",),
    "tcolorbox": ("tcolorbox.sty", "tcbbreakable.code.tex", "tcbskins.code.tex"),
    "fancyhdr": ("fancyhdr.sty",),
    "geometry": ("geometry.sty",),
    "hyperref": ("hyperref.sty",),
    "amsmath": ("amsmath.sty",),
    "amsfonts": ("amssymb.sty",),
}
GUIDE = "https://yihui.org/tinytex/"
ENGINES = ("pdflatex", "xelatex", "lualatex")
MAX_CANDIDATES, MAX_REPAIRS, MAX_PASSES = 3, 2, 3
PROBE_SECONDS, COMPILE_SECONDS, EXPORT_SECONDS = 15, 60, 120
OWNER_FILE = ".revision-comparison-managed.json"


class SetupError(Exception):
    pass


class CommandTimeout(SetupError):
    pass


class CommandFailed(SetupError):
    def __init__(self, command, returncode):
        super().__init__("Command exited {}: {}".format(returncode, command))
        self.returncode = returncode


class BudgetExpired(SetupError):
    pass


class CompanionMissing(SetupError):
    pass


class Deadline:
    def __init__(self, seconds=EXPORT_SECONDS, end=None):
        self.end = time.monotonic() + seconds if end is None else end

    def limit(self, seconds):
        remaining = self.end - time.monotonic()
        if remaining <= 0:
            raise BudgetExpired("The PDF export time budget is exhausted.")
        return min(seconds, remaining)

    def child(self, seconds):
        return Deadline(end=time.monotonic() + self.limit(seconds))


def managed_root():
    return Path.home() / ".local" / "share" / "revision-comparison" / "TinyTeX"


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def is_pdf(path):
    if not path.is_file():
        return False
    with path.open("rb") as source:
        return source.read(5) == b"%PDF-"


def companion(engine, name):
    for directory in dict.fromkeys([engine.parent, engine.resolve().parent]):
        for suffix in ("", ".exe", ".bat"):
            candidate = directory / (name + suffix)
            if candidate.is_file():
                return str(candidate)
    raise CompanionMissing("{} is missing beside {}.".format(name, engine))


def is_miktex(engine):
    try:
        companion(engine, "miktex")
        return True
    except CompanionMissing:
        return False


def kpsewhich_command(engine, *arguments, miktex=False):
    flags = ["--miktex-disable-installer", "--miktex-disable-maintenance"] if miktex or is_miktex(engine) else []
    return [companion(engine, "kpsewhich"), *flags, *arguments]


def engine_version(engine, deadline):
    flags = ["--miktex-disable-installer", "--miktex-disable-maintenance"] if is_miktex(engine) else []
    result = run([str(engine), *flags, "--version"], deadline=deadline, capture_output=True, text=True)
    return "miktex" in ((result.stdout or "") + (result.stderr or "")).lower()


def engine_candidates(preferred=None, unicode=False, private_only=False):
    """Enumerate known locations; keep engine aliases but deduplicate bin trees."""
    names = ("xelatex", "lualatex", "pdflatex") if unicode else ENGINES
    directories = [managed_root() / "bin"]
    bins = []
    if not private_only:
        bins = [Path(p).expanduser().absolute() for p in os.get_exec_path() if p]
        bins.append(Path("/Library/TeX/texbin"))
        directories += [Path.home() / ".TinyTeX" / "bin", Path.home() / "Library" / "TinyTeX" / "bin"]
        if os.environ.get("APPDATA"):
            directories.append(Path(os.environ["APPDATA"]) / "TinyTeX" / "bin")
        for variable in ("LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)"):
            if os.environ.get(variable):
                base = Path(os.environ[variable])
                if variable == "LOCALAPPDATA":
                    base /= "Programs"
                bins.append(base / "MiKTeX" / "miktex" / "bin" / "x64")
    for directory in directories:
        if directory.is_dir():
            bins.extend(sorted(p for p in directory.iterdir() if p.is_dir()))
    groups, seen = [], set()
    for directory in bins:
        if directory.resolve() in seen:
            continue
        seen.add(directory.resolve())
        group = []
        for name in names:
            found = shutil.which(name, path=str(directory))
            if found:
                group.append(Path(found).absolute())
        if group:
            groups.append(group)
    result = []
    if preferred:
        preferred = str(Path(preferred).expanduser())
        found = shutil.which(preferred) or (preferred if Path(preferred).is_file() else None)
        if found:
            result.append(Path(found).expanduser().absolute())
    # Cover different installations before spending probes on sibling engines.
    for index in range(len(names)):
        result.extend(group[index] for group in groups if len(group) > index)
    unique = {}
    for engine in result:
        key = (engine.resolve().parent, engine.stem.lower())
        unique.setdefault(key, engine)  # Preserve pdflatex's invoked name, not pdftex's target name.
    return list(unique.values())


def owned_engine(engine):
    root = managed_root()
    marker = root / OWNER_FILE
    try:
        return (not root.is_symlink() and not marker.is_symlink()
                and root.resolve() in Path(engine).resolve().parents
                and json.loads(marker.read_text()).get("owner") == "revision-comparison")
    except (OSError, ValueError):
        return False


def tex_environment(engine, cache=None):
    env = dict(os.environ)
    env["PATH"] = str(Path(engine).parent) + os.pathsep + env.get("PATH", "")
    if owned_engine(engine):
        user = managed_root() / "user"
        env.update(TEXMFHOME=str(user / "texmf"), TEXMFCONFIG=str(user / "config"),
                   TEXMFVAR=str(user / "var"), TEXMFCACHE=str(user / "cache"))
    if cache is not None:
        env.update(TEXMFVAR=str(Path(cache) / "texmf-var"), TEXMFCACHE=str(Path(cache) / "texmf-cache"))
    return env


def stop_process_tree(process):
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired):
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        for stream in (process.stdout, process.stderr):
            if stream:
                stream.close()
        process.wait(timeout=2)


def run(command, timeout=5, deadline=None, capture_output=False, text=False, **kwargs):
    duration = deadline.limit(timeout) if deadline else timeout
    env = kwargs.pop("env", None)
    if env is None:
        env = tex_environment(command[0])
    if capture_output:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    launch = {"creationflags": 0x00000200} if os.name == "nt" else {"start_new_session": True}
    try:
        process = subprocess.Popen(command, env=env, text=text, shell=False, **launch, **kwargs)
        try:
            stdout, stderr = process.communicate(timeout=duration)
        except subprocess.TimeoutExpired as error:
            stop_process_tree(process)
            raise CommandTimeout("Command exceeded {:.1f}s: {}".format(duration, command[0])) from error
        except BaseException:
            stop_process_tree(process)
            raise
        if process.returncode:
            raise CommandFailed(command, process.returncode)
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    except OSError as error:
        raise SetupError("Command failed: {} ({})".format(command, error)) from error


def missing_packages(engine, deadline=None, miktex=False):
    missing = []
    for package, filenames in PACKAGES.items():
        for filename in filenames:
            try:
                result = run(kpsewhich_command(engine, filename, miktex=miktex), deadline=deadline, capture_output=True, text=True)
                found = bool(result.stdout.strip())
            except (BudgetExpired, CommandTimeout):
                raise
            except CompanionMissing:
                raise
            except SetupError:
                found = False
            if not found:
                missing.append(package)
                break
    return missing


def install_packages(engine, packages):
    if not packages:
        return
    if not owned_engine(engine):
        raise SetupError("Existing TeX installations are read-only to this installer; only its marked private TinyTeX may receive packages.")
    print("Installing private LaTeX packages: {}".format(", ".join(packages)), flush=True)
    tlmgr = companion(engine, "tlmgr")
    root = run(kpsewhich_command(engine, "-var-value=TEXMFROOT"), capture_output=True, text=True).stdout.strip()
    if Path(root).resolve() != managed_root().resolve():
        raise SetupError("The package manager points outside the private TinyTeX directory; preserved.")
    run([tlmgr, "install", *packages], timeout=600)


def bundle_name():
    system, machine = platform.system(), platform.machine().lower()
    if system == "Darwin":
        return "TinyTeX-1-darwin.tar.xz"
    if system == "Windows":
        return "TinyTeX-1-windows.exe"
    if system == "Linux":
        musl = platform.libc_ver()[0] == "musl" or any(Path("/lib").glob("libc.musl-*.so.1"))
        if machine in ("x86_64", "amd64"):
            return "TinyTeX-1-{}-x86_64.tar.xz".format("linuxmusl" if musl else "linux")
        if machine in ("aarch64", "arm64") and not musl:
            return "TinyTeX-1-linux-arm64.tar.xz"
    raise SetupError("Automatic LaTeX installation is unavailable on this platform. See " + GUIDE)


def extract_bundle(archive, destination):
    destination = destination.resolve()
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            if Path(member.name).is_absolute():
                raise SetupError("Absolute path in the LaTeX archive: " + member.name)
            target = (destination / member.name).resolve()
            if destination not in target.parents and target != destination:
                raise SetupError("Unsafe path in the LaTeX archive: " + member.name)
            if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                raise SetupError("Unsupported archive entry: " + member.name)
            if member.issym() or member.islnk():
                if Path(member.linkname).is_absolute():
                    raise SetupError("Absolute link in the LaTeX archive: " + member.name)
                base = target.parent if member.issym() else destination
                link = (base / member.linkname).resolve()
                if destination not in link.parents:
                    raise SetupError("Unsafe link in the LaTeX archive: " + member.name)
            if hasattr(tarfile, "data_filter"):
                bundle.extract(member, destination, filter="data")
            else:
                bundle.extract(member, destination)


def install_tinytex():
    target = managed_root()
    if os.path.lexists(target):
        raise SetupError("Existing LaTeX directory preserved: {}. Repair it before retrying.".format(target))
    filename = bundle_name()
    if platform.system() != "Windows" and not shutil.which("perl"):
        raise SetupError("TinyTeX needs Perl for package installation. Install Perl with your system package manager, then retry.")
    scratch = Path(tempfile.mkdtemp(prefix="revision-comparison-latex-"))
    archive = scratch / filename
    url = "https://github.com/rstudio/tinytex-releases/releases/download/daily/" + filename
    print("Installing LaTeX (TinyTeX) in {}".format(target), flush=True)
    print("Downloading {}\nSetup files: {}".format(url, scratch), flush=True)
    download_deadline = Deadline(600)
    with urlopen(url, timeout=60) as response, archive.open("xb") as output:
        while True:
            download_deadline.limit(60)
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
    if filename.endswith(".exe"):
        run([str(archive), "-y"], timeout=600, cwd=str(scratch))
    else:
        extract_bundle(archive, scratch)
    tree = scratch / (".TinyTeX" if platform.system() == "Linux" else "TinyTeX")
    if not (tree / "bin").is_dir():
        raise SetupError("The downloaded archive has no TinyTeX toolchain. Setup files retained at {}".format(scratch))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir()  # Exclusive creation; never replace an existing toolchain.
    shutil.copytree(tree, target, dirs_exist_ok=True, symlinks=True)
    with (target / OWNER_FILE).open("x", encoding="utf-8") as marker:
        json.dump({"owner": "revision-comparison", "schema": 1}, marker)
    candidates = engine_candidates(private_only=True)
    if not candidates:
        raise SetupError("LaTeX files were retained at {}, but no compiler was found.".format(target))
    return candidates[0]


def check_build(engine, deadline=None, directory=None, miktex=False):
    scratch = directory or Path(tempfile.mkdtemp(prefix="revision-comparison-pdf-check-"))
    scratch.mkdir(parents=True, exist_ok=True)
    for name in ("annotations.tex", "comparison-style.tex"):
        shutil.copy2(SKILL / "assets" / name, scratch / name)
    source = r"""\documentclass{article}
\usepackage[a4paper,margin=20mm]{geometry}
\usepackage{amsmath,amssymb,hyperref}
\input{annotations.tex}
\input{comparison-style.tex}
\begin{document}
\rcReportTitle{Revision Comparison}{PDF setup check}
\begin{rcContext}{Context}The timing excludes feature precomputation.\end{rcContext}
\begin{rcPassage}{C1}{BEFORE}{Summary}
The method reduces \rcrewrite{optimization} time by 38\%.
\end{rcPassage}
\begin{rcPassage}{C1}{AFTER}{Summary}
The method reduces \rcrewrite{end-to-end training} time by 38\%.
\[F(\theta)=\frac{1}{2n}\|X\theta-y\|_2^2+\frac{\lambda}{2}\|\theta\|_2^2.\]
\end{rcPassage}
\end{document}
"""
    (scratch / "check.tex").write_text(source, encoding="utf-8")
    flags = ["--disable-installer", "--disable-write18", "--miktex-disable-maintenance"] if miktex or is_miktex(engine) else ["-no-shell-escape"]
    try:
        with (scratch / "build-output.txt").open("w", encoding="utf-8") as log:
            run([str(engine), *flags, "-interaction=nonstopmode", "-halt-on-error", "check.tex"],
                timeout=COMPILE_SECONDS, deadline=deadline, env=tex_environment(engine, scratch),
                cwd=str(scratch), stdout=log, stderr=subprocess.STDOUT)
    except SetupError as error:
        raise SetupError("Theme check failed. Build files: {}. {}".format(scratch, error)) from error
    pdf = scratch / "check.pdf"
    if not is_pdf(pdf):
        raise SetupError("LaTeX did not produce a PDF. Build files: {}".format(scratch))
    return pdf


def select_engine(preferred=None, unicode=False, candidates=None):
    deadline = Deadline()
    candidates = engine_candidates(preferred, unicode) if candidates is None else candidates
    if not candidates:
        raise SetupError("No LaTeX compiler was found on PATH or in the known installation directories.")
    scratch = Path(tempfile.mkdtemp(prefix="revision-comparison-pdf-checks-"))
    errors, blocked, tried = [], set(), 0
    for engine in candidates:
        group = engine.resolve().parent
        if group in blocked:
            continue
        if tried >= MAX_CANDIDATES:
            break
        tried += 1
        probe = deadline.child(PROBE_SECONDS)
        try:
            miktex = engine_version(engine, probe)
            try:
                missing = missing_packages(engine, probe, miktex)
            except CompanionMissing:
                missing = []  # A wrapper may lack kpsewhich; the actual build is decisive.
            if missing:
                blocked.add(group)
                raise SetupError("Missing theme packages: " + ", ".join(missing))
            pdf = check_build(engine, probe, scratch / "candidate-{}".format(tried), miktex)
            return engine, pdf
        except SetupError as error:
            errors.append("{}: {}".format(engine, error))
    raise SetupError("No usable LaTeX candidate passed. {}. Check files: {}".format("; ".join(errors), scratch))


class BuildFailure(SetupError):
    def __init__(self, reason, environment=False, shared_dependency=False):
        super().__init__(reason)
        self.environment = environment
        self.shared_dependency = shared_dependency


def compile_document(engine, source, build, deadline, miktex=False):
    flags = ["--disable-installer", "--disable-write18", "--miktex-disable-maintenance"] if miktex or is_miktex(engine) else ["-no-shell-escape"]
    for number in range(1, MAX_PASSES + 1):
        output = build / "pass-{}.txt".format(number)
        try:
            with output.open("w", encoding="utf-8") as log:
                run([str(engine), *flags, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
                     "-recorder", "-jobname=comparison", "-output-directory=" + str(build), str(source)],
                    timeout=COMPILE_SECONDS, deadline=deadline, cwd=str(source.parent.parent),
                    env=tex_environment(engine, build), stdout=log, stderr=subprocess.STDOUT)
        except (BudgetExpired, CommandTimeout):
            raise
        except SetupError as error:
            detail = output.read_text(errors="replace")[-8000:]
            dependency = "not found" in detail and any(ext in detail for ext in (".sty", ".cls", ".def", ".fd", ".code.tex"))
            abnormal_exit = isinstance(error, CommandFailed) and error.returncode != 1
            environment = abnormal_exit or dependency or any(term in detail for term in (
                "Unicode character", "requires either XeTeX", "requires either LuaTeX",
                "can't find the format", "Fatal format file")) or not detail.strip()
            raise BuildFailure("{}. Build log: {}".format(error, output), environment, dependency) from error
        detail = output.read_text(errors="replace")
        if "Missing character:" in detail:
            raise BuildFailure("The selected fonts have missing glyphs. Build log: " + str(output))
        rerun = any(term in detail for term in ("Rerun to get", "Label(s) may have changed", "Please rerun LaTeX"))
        if not rerun:
            break
    else:
        raise BuildFailure("References did not settle within {} passes. Logs: {}".format(MAX_PASSES, build))
    pdf = build / "comparison.pdf"
    if not is_pdf(pdf):
        raise BuildFailure("The build produced no PDF. Logs: " + str(build))
    return pdf, [line.strip() for line in detail.splitlines() if "Warning" in line or "Overfull" in line]


def render_previews(pdf, build, deadline):
    renderer = shutil.which("pdftoppm")
    if not renderer:
        return [], "renderer-unavailable"
    try:
        run([renderer, "-scale-to", "1400", "-png", str(pdf), str(build / "page")],
            timeout=30, deadline=deadline, capture_output=True, text=True)
        status = "rendered; visual inspection still required"
    except SetupError as error:
        status = "preview-incomplete: " + str(error)
    return [str(p) for p in sorted(build.glob("page-*.png"))], status


def compile_report(source, preferred=None, unicode=False):
    """Persist one report's budget across at most two source-repair rounds."""
    source = source.expanduser().absolute()
    contents = source.read_bytes()
    digest = hashlib.sha256(contents).hexdigest()
    state_path = source.with_name("." + source.stem + ".pdf-build.json")
    lock = state_path.with_suffix(".lock")
    token = "{}:{}".format(os.getpid(), time.monotonic())
    try:
        with lock.open("x") as stream:
            stream.write(token)
    except FileExistsError as error:
        raise SetupError("A build lock already exists; preserved: " + str(lock)) from error
    try:
        state = {"owner": "revision-comparison", "schema": 1, "source": str(source), "remaining_seconds": EXPORT_SECONDS,
                 "repairs": 0, "attempt": 0, "tex_hash": digest}
        existing = os.path.lexists(state_path)
        if existing:
            if state_path.is_symlink():
                raise SetupError("Existing build-state link preserved: " + str(state_path))
            state = json.loads(state_path.read_text())
            valid = (state.get("owner") == "revision-comparison" and state.get("schema") == 1
                     and state.get("source") == str(source)
                     and isinstance(state.get("remaining_seconds"), (int, float))
                     and math.isfinite(state["remaining_seconds"]) and 0 <= state["remaining_seconds"] <= EXPORT_SECONDS
                     and isinstance(state.get("repairs"), int) and 0 <= state["repairs"] <= MAX_REPAIRS
                     and isinstance(state.get("attempt"), int) and state["attempt"] >= 0
                     and state.get("status") in ("pdf-ready", "needs-repair", "markdown-fallback"))
            if not valid:
                raise SetupError("Unrelated build state preserved: " + str(state_path))
            # Inputs and styles may change without changing the wrapper. Always rebuild;
            # another invocation consumes a retry rather than reusing a potentially stale PDF.
        if (existing and state["repairs"] >= MAX_REPAIRS) or state["remaining_seconds"] <= 0:
            state.update(status="markdown-fallback", reason="The report's repair or time budget is exhausted.")
            state_path.write_text(json.dumps(state, indent=2) + "\n")
            return state
        if existing:
            state["repairs"] += 1
        started = time.monotonic()
        deadline = Deadline(min(EXPORT_SECONDS, state["remaining_seconds"]))
        state.update(tex_hash=digest, attempt=state["attempt"] + 1, pdf=None, previews=[], preview_status="not-run",
                     status="markdown-fallback", reason="The previous build was interrupted.")
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        try:
            blocked, errors, tried = set(), [], 0
            candidates = engine_candidates(preferred or state.get("compiler"), unicode)
            for engine in candidates:
                group = engine.resolve().parent
                if group in blocked:
                    continue
                if tried >= MAX_CANDIDATES:
                    break
                tried += 1
                try:
                    miktex = engine_version(engine, deadline.child(PROBE_SECONDS))
                except BudgetExpired:
                    raise
                except SetupError as error:
                    errors.append("{}: {}".format(engine, error))
                    continue
                build = Path(tempfile.mkdtemp(prefix=".pdf-build-", dir=str(source.parent)))
                frozen = build / "comparison.tex"
                frozen.write_bytes(contents)
                state["build_directory"] = str(build)
                try:
                    pdf, warnings = compile_document(engine, frozen, build, deadline, miktex)
                except BudgetExpired:
                    raise
                except CommandTimeout as error:
                    errors.append("{}: {}".format(engine, error))
                    continue
                except BuildFailure as error:
                    errors.append("{}: {}".format(engine, error))
                    if error.shared_dependency:
                        blocked.add(group)
                    if error.environment:
                        continue
                    state.update(status="needs-repair" if state["repairs"] < MAX_REPAIRS else "markdown-fallback",
                                 reason=str(error), compiler=str(engine))
                    break
                destination = source.with_suffix(".pdf")
                suffix = 1
                while os.path.lexists(destination):
                    destination = source.with_name("{}-{}.pdf".format(source.stem, suffix))
                    suffix += 1
                with destination.open("xb") as output:
                    with pdf.open("rb") as input_pdf:
                        shutil.copyfileobj(input_pdf, output)
                state.update(status="pdf-ready", reason=None, compiler=str(engine), pdf=str(destination), warnings=warnings,
                             pdf_hash=file_hash(destination))
                state["previews"], state["preview_status"] = render_previews(destination, build, deadline)
                break
            else:
                state.update(status="markdown-fallback", reason="; ".join(errors) or "No LaTeX compiler was found.")
            if state["reason"] == "The previous build was interrupted.":
                state["reason"] = "; ".join(errors) or "No usable compiler passed within the candidate limit."
        except SetupError as error:
            state.update(status="markdown-fallback", reason=str(error))
        finally:
            state["remaining_seconds"] = max(0, state["remaining_seconds"] - (time.monotonic() - started))
            state_path.write_text(json.dumps(state, indent=2) + "\n")
        return state
    finally:
        try:
            if lock.read_text() == token:
                lock.unlink()  # Only the lock created by this invocation is removed.
        except OSError:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check the comparison theme, or install its LaTeX dependencies.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Check only; never download or install anything (default).")
    mode.add_argument("--install", action="store_true", help="Reuse existing LaTeX or prepare the marked private TinyTeX; never modify another distribution.")
    mode.add_argument("--compile", type=Path, metavar="REPORT.tex", help="Compile a generated comparison wrapper with bounded retries; never install software.")
    parser.add_argument("--engine", help="Preferred compiler name or path, including a previously successful compiler.")
    parser.add_argument("--unicode", action="store_true", help="Prefer XeLaTeX/LuaLaTeX for Unicode report text.")
    args = parser.parse_args(argv)
    try:
        if args.compile:
            result = compile_report(args.compile, args.engine, args.unicode)
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "pdf-ready" else 1
        try:
            engine, pdf = select_engine(args.engine, args.unicode)
        except SetupError:
            if not args.install:
                raise
            if os.path.lexists(managed_root()):
                candidates = engine_candidates(unicode=args.unicode, private_only=True)
                if not candidates or not owned_engine(candidates[0]):
                    raise SetupError("Existing private-path contents are unmarked or incomplete; preserved: " + str(managed_root()))
                engine = candidates[0]
            else:
                engine = install_tinytex()
            install_packages(engine, missing_packages(engine, Deadline(PROBE_SECONDS)))
            engine, pdf = select_engine(args.engine, args.unicode, engine_candidates(private_only=True, unicode=args.unicode))
    except (SetupError, OSError, ValueError, tarfile.TarError) as error:
        print("PDF setup incomplete: {}\nMarkdown reports are still available.".format(error), file=sys.stderr)
        return 1
    print("PDF export is ready. LaTeX compiler: {}\nTest PDF: {}".format(engine, pdf))
    print("Use this compiler's full path if it is not on PATH; no shell configuration was changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
