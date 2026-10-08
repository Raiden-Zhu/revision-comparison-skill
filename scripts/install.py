#!/usr/bin/env python3
"""Install the local Revision Comparison skill. MIT; see ../LICENSE."""

import argparse
import os
from pathlib import Path
import shutil
import sys


SKILL_NAME = "revision-comparison"
SOURCE = Path(__file__).resolve().parent.parent / "skills" / SKILL_NAME


def parser():
    result = argparse.ArgumentParser(
        description="Copy the complete local skill into a new installation directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Destinations (each ends in revision-comparison):
  codex / user:          ~/.agents/skills/revision-comparison
  codex / project:       PROJECT/.agents/skills/revision-comparison
  claude-code / user:    ~/.claude/skills/revision-comparison
  claude-code / project: PROJECT/.claude/skills/revision-comparison

Examples:
  python3 scripts/install.py
  python3 scripts/install.py --agent claude-code
  python3 scripts/install.py --scope project --project "/path with spaces/project"
  python3 scripts/install.py --dest "/custom/skills/revision-comparison"

Existing destinations, including symbolic links, are never overwritten.
Copy failures retain the partial installation and report its location.
""",
    )
    result.add_argument("--agent", choices=("codex", "claude-code"), default="codex")
    result.add_argument("--scope", choices=("user", "project"), default="user")
    result.add_argument("--project", type=Path, help="Existing project directory; required for project scope unless --dest is used.")
    result.add_argument("--dest", type=Path, help="Exact installation directory; overrides agent/scope destinations.")
    return result


def absolute(path):
    # Do not resolve the final component: a dangling symlink is an existing target.
    return Path(os.path.abspath(path.expanduser()))


def destination(args, argument_parser):
    if args.dest is not None:
        return absolute(args.dest)
    if args.scope == "project":
        if args.project is None:
            argument_parser.error("--scope project requires --project or --dest")
        project = absolute(args.project)
        if not project.is_dir():
            argument_parser.error("project directory does not exist: {}".format(project))
        host = ".agents" if args.agent == "codex" else ".claude"
        return project / host / "skills" / SKILL_NAME
    if args.project is not None:
        argument_parser.error("--project requires --scope project")
    if args.agent == "codex":
        return absolute(Path.home()) / ".agents" / "skills" / SKILL_NAME
    return absolute(Path.home()) / ".claude" / "skills" / SKILL_NAME


def main(argv=None):
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    target = destination(args, argument_parser)
    if not (SOURCE / "SKILL.md").is_file():
        print("Skill source is missing: {}".format(SOURCE / "SKILL.md"), file=sys.stderr)
        return 1
    if os.path.lexists(target):
        print("Installation already exists; preserved: {}".format(target), file=sys.stderr)
        return 1
    resolved_target = target.parent.resolve() / target.name
    if SOURCE == resolved_target or SOURCE in resolved_target.parents:
        print("Destination must be outside the skill source: {}".format(target), file=sys.stderr)
        return 1
    created = False
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir()  # Exclusive creation also catches a competing installation.
        created = True
        shutil.copytree(SOURCE, target, dirs_exist_ok=True)
    except FileExistsError as error:
        if not created:
            print("Installation path already exists; preserved: {} ({})".format(target, error), file=sys.stderr)
        else:
            print("Copy failed; partial installation retained at {}: {}".format(target, error), file=sys.stderr)
        return 1
    except (OSError, shutil.Error) as error:
        if created:
            print("Copy failed; partial installation retained at {}: {}".format(target, error), file=sys.stderr)
        else:
            print("Could not create installation at {}: {}".format(target, error), file=sys.stderr)
        return 1
    print("Installed {} at {}".format(SKILL_NAME, target))
    print("Start a new agent session or follow its skill reload instructions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
