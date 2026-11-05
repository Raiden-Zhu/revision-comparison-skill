#!/usr/bin/env python3
"""Check or install LaTeX for the comparison theme. MIT; see repository LICENSE."""

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
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


class SetupError(Exception):
    pass


def managed_root():
    return Path.home() / ".local" / "share" / "revision-comparison" / "TinyTeX"


def companion(engine, name):
    for suffix in ("", ".exe", ".bat"):
        candidate = engine.parent / (name + suffix)
        if candidate.is_file():
            return str(candidate)
    raise SetupError("{} is missing beside {}. Repair this LaTeX installation first.".format(name, engine))


def is_miktex(engine):
    try:
        companion(engine, "miktex")
        return True
    except SetupError:
        return False


def kpsewhich_command(engine, *arguments):
    flags = ["--miktex-disable-installer", "--miktex-disable-maintenance"] if is_miktex(engine) else []
    return [companion(engine, "kpsewhich"), *flags, *arguments]


def find_engine():
    directories = [managed_root() / "bin"]
    directories += [Path.home() / ".TinyTeX" / "bin", Path.home() / "Library" / "TinyTeX" / "bin"]
    if os.environ.get("APPDATA"):
        directories.append(Path(os.environ["APPDATA"]) / "TinyTeX" / "bin")
    bins = [Path("/Library/TeX/texbin")]
    for directory in directories:
        if directory.is_dir():
            bins.extend(sorted(p for p in directory.iterdir() if p.is_dir()))
    for name in ("pdflatex", "xelatex", "lualatex"):
        found = shutil.which(name)
        if found:
            return Path(found)
    for directory in bins:
        for name in ("pdflatex", "xelatex", "lualatex"):
            found = shutil.which(name, path=str(directory))
            if found:
                return Path(found)
    return None


def run(command, **kwargs):
    env = dict(os.environ)
    env["PATH"] = str(Path(command[0]).parent) + os.pathsep + env.get("PATH", "")
    try:
        return subprocess.run(command, env=env, check=True, **kwargs)
    except (OSError, subprocess.CalledProcessError) as error:
        raise SetupError("Command failed: {} ({})".format(command, error)) from error


def missing_packages(engine):
    missing = []
    for package, filenames in PACKAGES.items():
        for filename in filenames:
            result = subprocess.run(kpsewhich_command(engine, filename), capture_output=True, text=True)
            if result.returncode or not result.stdout.strip():
                missing.append(package)
                break
    return missing


def install_packages(engine, packages):
    if not packages:
        return
    print("Installing missing LaTeX packages: {}".format(", ".join(packages)), flush=True)
    try:
        tlmgr = companion(engine, "tlmgr")
    except SetupError:
        manager = companion(engine, "miktex")
        run([manager, "packages", "install", *packages])
        return
    root = run(kpsewhich_command(engine, "-var-value=TEXMFROOT"), capture_output=True, text=True).stdout.strip()
    database = Path(root) / "tlpkg" / "texlive.tlpdb"
    options = []
    if not root or not database.is_file():
        raise SetupError("Cannot identify the TeX Live package database; repair the existing installation first.")
    if not os.access(database, os.W_OK):
        home = run(kpsewhich_command(engine, "-var-value=TEXMFHOME"), capture_output=True, text=True).stdout.strip()
        if not home or not Path(home).is_absolute():
            raise SetupError("Cannot identify a user-local TeX tree for missing packages.")
        options = ["--usermode"]
        if not (Path(home) / "tlpkg" / "texlive.tlpdb").exists():
            run([tlmgr, *options, "init-usertree"])
    run([tlmgr, *options, "install", *packages])


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
    with urlopen(url, timeout=60) as response, archive.open("xb") as output:
        shutil.copyfileobj(response, output)
    if filename.endswith(".exe"):
        run([str(archive), "-y"], cwd=str(scratch))
    else:
        extract_bundle(archive, scratch)
    tree = scratch / (".TinyTeX" if platform.system() == "Linux" else "TinyTeX")
    if not (tree / "bin").is_dir():
        raise SetupError("The downloaded archive has no TinyTeX toolchain. Setup files retained at {}".format(scratch))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir()  # Exclusive creation; never replace an existing toolchain.
    shutil.copytree(tree, target, dirs_exist_ok=True, symlinks=True)
    engine = find_engine()
    if engine is None:
        raise SetupError("LaTeX files were retained at {}, but no compiler was found.".format(target))
    return engine


def check_build(engine):
    scratch = Path(tempfile.mkdtemp(prefix="revision-comparison-pdf-check-"))
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
    flags = ["--disable-installer", "--disable-write18", "--miktex-disable-maintenance"] if is_miktex(engine) else ["-no-shell-escape"]
    try:
        with (scratch / "build-output.txt").open("w", encoding="utf-8") as log:
            run([str(engine), *flags, "-interaction=nonstopmode", "-halt-on-error", "check.tex"],
                cwd=str(scratch), stdout=log, stderr=subprocess.STDOUT)
    except SetupError as error:
        raise SetupError("Theme check failed. Build files: {}. {}".format(scratch, error)) from error
    pdf = scratch / "check.pdf"
    if not pdf.is_file() or not pdf.read_bytes().startswith(b"%PDF-"):
        raise SetupError("LaTeX did not produce a PDF. Build files: {}".format(scratch))
    return pdf


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check the comparison theme, or install its LaTeX dependencies.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Check only; never download or install anything (default).")
    mode.add_argument("--install", action="store_true", help="Install LaTeX if absent, or add the theme's missing packages.")
    args = parser.parse_args(argv)
    try:
        engine = find_engine()
        if engine is None:
            if not args.install:
                raise SetupError("LaTeX was not found. Run this script with --install to enable PDF export.")
            engine = install_tinytex()
        missing = missing_packages(engine)
        if missing and args.install:
            install_packages(engine, missing)
            missing = missing_packages(engine)
        if missing:
            raise SetupError("Missing LaTeX packages: {}. Run this script with --install.".format(", ".join(missing)))
        print("Checking the PDF theme with {}".format(engine), flush=True)
        pdf = check_build(engine)
    except (SetupError, OSError, tarfile.TarError) as error:
        print("PDF setup incomplete: {}\nMarkdown reports are still available.".format(error), file=sys.stderr)
        return 1
    print("PDF export is ready. LaTeX compiler: {}\nTest PDF: {}".format(engine, pdf))
    print("Use this compiler's full path if it is not on PATH; no shell configuration was changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
