# Revision Comparison

Review a revision where the original, revised passage, and reason appear together.

Revision Comparison is a skill for file-reading and file-writing agents. It produces a separate review document with faithful before-and-after quotations, stable change IDs, locations, localized highlights, and explanations. It is useful for paper revisions, technical reports, and other documents whose wording and meaning need to remain traceable.

```text
C1 · Method / feature extraction
Context: The extractor is frozen; the gate is trainable.
Before: “It acts on the features.”
After:  “The gate acts on the features.”
Reason: Proposed wording names the component instead of relying on “It.”
```

The skill can compare a revision you already have or propose a revision for comparison. Applying selected edits to the source is a separate, explicitly requested action.

## What you get

- A report overview stating the revision goal, scope, and constraints.
- Local before-and-after pairs, with enough real context to read each change.
- A change map linking IDs to source and revised locations.
- Concrete reasons, distinguished from inferred explanations of someone else's edits.
- A scoped account of meaning changes, verification limits, and unresolved concerns.

Markdown is the default output. A PDF can accompany it when a working LaTeX toolchain and rendered-page inspection are available. Editable source remains part of that export.

See the [language-edit example](examples/language-edit/comparison.md), [structure-edit example](examples/structure-edit/comparison.md), [semantic-review example](examples/semantic-review/comparison.md), and [math example](examples/math/comparison.md). These examples use synthetic material.

## Install

The installable skill lives in [`skills/revision-comparison`](skills/revision-comparison), rather than the repository root. Copy the entire directory so its references and annotation assets remain available.

### Codex

With the skill installer available, ask your agent:

```text
Use skill-installer to install revision-comparison from
https://github.com/Raiden-Zhu/revision-comparison-skill,
using the repository path skills/revision-comparison.
If that skill is already installed, stop and report its location.
```

Alternatively, clone this repository into a new directory:

```sh
git clone https://github.com/Raiden-Zhu/revision-comparison-skill.git
cd revision-comparison-skill
```

Run the following from its root. The destination is `${CODEX_HOME:-$HOME/.codex}/skills/revision-comparison`. An existing installation is preserved.

```sh
skill_parent="${CODEX_HOME:-$HOME/.codex}/skills"
skill_target="$skill_parent/revision-comparison"
if [ -e "$skill_target" ] || [ -L "$skill_target" ]; then
  printf 'Installation already exists: %s\n' "$skill_target"
else
  mkdir -p "$skill_parent" &&
    cp -R ./skills/revision-comparison "$skill_target"
fi
```

The source directory in this command is the skill inside your cloned repository. Start a new session or follow your agent's skill reload instructions after installation.

### Claude Code

For a project installation, run this from the repository root, replacing `/absolute/path/to/project` with your project directory:

```sh
project_skill_parent="/absolute/path/to/project/.claude/skills"
project_skill_target="$project_skill_parent/revision-comparison"
if [ -e "$project_skill_target" ] || [ -L "$project_skill_target" ]; then
  printf 'Installation already exists: %s\n' "$project_skill_target"
else
  mkdir -p "$project_skill_parent" &&
    cp -R ./skills/revision-comparison "$project_skill_target"
fi
```

### Other agents

Ask the agent to read [`SKILL.md`](skills/revision-comparison/SKILL.md) and follow its relative references. Automatic skill discovery depends on the host. This repository provides instructions and assets; it does not provide a standalone revision CLI.

## Compare an existing revision

Use `compare` when you have both versions. The agent compares the supplied text rather than polishing the revised version again.

```text
Use revision-comparison in compare mode.
Before: drafts/method-v1.tex
After: drafts/method-v2.tex
Scope: the feature-extraction subsection.
Produce a separate Markdown comparison in review/method-comparison/.
Explain the differences in English. Preserve both supplied versions.
```

Reasons supplied by the author can be included as provided reasons. When the agent interprets an edit without an author explanation, the report should identify the reason as inferred. An inference about intent is not evidence that the author intended it.

## Propose a revision and compare it

Use `propose-and-compare` when you want a new draft. State the editing scope and the concrete problem to solve.

```text
Use revision-comparison in propose-and-compare mode on paper/method.tex.
Scope: the feature-extraction subsection.
Editing scope: language-only.
Goal: clarify which operation acts on the frozen features.
Preserve the claims, notation, equations, numbers, and citations.
Use the optional academic style profile.
Produce a separate Markdown comparison in review/method-proposal/.
Do not apply the proposal to the manuscript.
```

The writing step produces one proposed version; the comparison then traces that same version. The optional profile guides prose choices without starting another independent rewrite.

For grammar correction, use a narrower brief within language-only editing:

```text
Editing scope: language-only.
Brief: correct grammar and punctuation only; retain sentence structure
where possible and preserve the author's terminology and voice.
```

For structural work, name the allowed section and the organizational goal. Scientific revision requires access to the relevant support. The [core instructions](skills/revision-comparison/SKILL.md) define these editing boundaries.

## Apply selected edits

Applying changes is independent of the two content modes. Request it explicitly and identify the version or changes to apply.

```text
Apply C1 and C3 from review/method-proposal/comparison.md to
paper/method.tex. Keep the remaining passages as they are.
Preserve a baseline and deliver a clean manuscript.
```

If you want annotations inside an English manuscript, request them separately. The skill can use switchable annotations and English revision notes for supported LaTeX workflows. Approving a clean integration does not automatically request visible review notes.

## Read the report

The overview explains what the revision is trying to achieve and what it covers. Each change unit then identifies the passage's role in its section and supplies only the definitions or neighboring context needed to understand that particular edit.

Context comes from the supplied document or supporting material. Quote a needed definition or neighboring passage with its location; a distant assumption may need its own source pointer. Label an editor summary as a summary and an assigned section role as an editorial judgment. Neither replaces the exact before-and-after quotations, including any original errors. If required context is unavailable, report that limit rather than inventing a condition. Repeating the overview under every change makes a report harder to read.

Each unit keeps the original passage, revised passage, and reason close together. Locations combine a section with a faithful anchor; reliable line numbers or paragraph IDs can supplement it. Stable IDs let you discuss or approve a change without searching for it again.

| Label | Presentation | Meaning |
| --- | --- | --- |
| Added | Blue text | New content, with insertion context |
| Rewritten | Purple text | Replaced wording or content |
| Moved/Reformatted | Black content, green annotation | A location or presentation change |
| Deleted | Original passage and a deletion reason | Content removed from the revision |
| Unchanged | Black text | Retained content |

Labels and IDs carry the meaning even when colors are unavailable. Markdown renderers vary in their support for colored text; the report remains readable without color.

A reason should name the problem and benefit: an undefined term, unclear referent, repeated explanation, changed comparator, or removed condition. “More academic” alone does not explain an edit.

For whole-document comparisons, a coverage summary identifies which sections were compared, retained, or excluded. A local comparison does not imply a full-paper audit.

## Meaning and confidence

The report distinguishes exposition changes, equivalent reformulations, substantive changes, and uncertain cases. These descriptions do not by themselves certify scientific correctness. Verification status records what could actually be checked from the available sources.

Preserve justified confidence as well as justified uncertainty. Missing evidence or context does not authorize silent weakening; flag what remains unverified. A theorem can retain proof language, while an empirical interpretation still needs its measured scope.

Checks focus on the changed units and the context needed to assess them, including distant definitions or conditions. When a revision changes an assumption, inequality, comparison, or result value, the report makes that change visible and checks its support within the requested scope. It does not invent an experiment or silently expand into a manuscript-wide scientific review.

## Optional academic style

The [academic style profile](skills/revision-comparison/references/academic-style.md) supports author voice, direct prose, readable formalism, concise reasoning, and continuity between passages. It is optional and applies when proposing revisions.

Academic-Humanizer and research-paper-writing informed the separation between prose preferences and editing permissions. The profile is self-contained; neither skill is required to install or use it. It supports academic clarity rather than AI-detection or disclosure avoidance.

Public documentation is in English. Manuscript language follows the target document, and comparison explanations can use the language you request.

## Formats and limits

- **Markdown:** the default, editable comparison artifact.
- **LaTeX/PDF:** an optional export with isolated labels/counters, compilation checks, and rendered-page inspection. See [rendering guidance](skills/revision-comparison/references/rendering.md).
- **Other documents:** use the host's available reading and export capabilities. Native Word Track Changes is not implemented by this repository.

The skill needs readable source material. If a reference, formula, or passage cannot be recovered faithfully, the agent should disclose the limitation rather than reconstruct it from a guess. Successful compilation validates rendering, not scientific claims.

## Repository layout

```text
skills/revision-comparison/
  SKILL.md
  agents/openai.yaml
  references/academic-style.md
  references/rendering.md
  assets/annotations.tex
examples/
  language-edit/       before, after, comparison
  structure-edit/      before, after, comparison
  semantic-review/    before, after, comparison
  math/               before, after, comparison
evaluations/cases.md
LICENSE
```

The [evaluation cases](evaluations/cases.md) cover representative failure modes without requiring a separate evaluation framework. Contributions should use synthetic or explicitly shareable material and keep the core contract as the authority for editing permissions and fidelity.

## License

MIT. See [LICENSE](LICENSE).
