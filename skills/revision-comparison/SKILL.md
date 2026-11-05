---
name: revision-comparison
description: Create contextual before-and-after comparisons with exact passages, locations, highlighted changes, and explanations. Use to review existing document revisions or to propose bounded edits with a separate comparison. Preserve supplied versions; apply a selected revision only when requested.
---

# Revision Comparison

Make revisions easy to review: show the passage, enough context to understand its role, the corresponding revision, and what the change affects. Produce a separate comparison by default.

## Choose the task

- **Compare:** the user provides an original and a revised version. Compare those versions faithfully, including any errors. Do not generate a third version; report concerns separately.
- **Propose and compare:** the user provides an original and an editing goal. Make one revision within that scope, then use that same revision throughout the comparison. Load the [academic style profile](references/academic-style.md) when useful for academic editing.
- If neither a revised version nor an editing goal is available, clarify the missing input. A request for a comparison alone does not imply a rewrite.

Distinguish the content mode from the edit scope. Polishing defaults to **language-only**: preserve scientific meaning and document structure. Structural editing may reorganize the authorized passages. Scientific revision requires relevant evidence before changing claims or mathematics. Grammar-only is a narrower editing brief, not a separate mode.

Preserve claims, comparisons, assumptions, quantifiers, numbers, equations, citation attribution, terminology, and justified confidence or uncertainty during language editing. Missing context means unverified, not false; flag suspected scientific problems without silently weakening the text. In compare mode, describe substantive differences without silently correcting either version.

## Establish the baseline

Read the current source and the relevant surrounding material. For a multi-file manuscript, follow its actual inclusion order. Reading a definition outside the selected section supplies context, not permission to edit that section.

Create a new output directory. Preserve the compared source files or supplied text as snapshots; record their identities, scope, and SHA-256 hashes. Hashes identify bytes, not scientific validity. When macros, included files, or a bibliography affect interpretation or rendering, record the dependencies actually used and any unavailable ones; do not claim that unrecorded dependencies are frozen.

Keep supplied versions and earlier comparison packages unchanged. For proposed edits, save the authoritative revised text separately from presentation markup. Avoid another rewrite while producing the comparison or a clean export.

## Build the comparison

Open with a short orientation: what the document or section does, the user's revision goal, the selected scope and constraints, the two version identities, and the comparison granularity. State covered and omitted sections or unresolved mappings. Do not invent a manuscript purpose from a fragment.

Use a compact change index for a long report. Assign IDs such as C1 and C2, stable within this comparison package. Each change unit contains:

1. **Context, when needed.** Explain the passage's editor-assigned role briefly. Quote unchanged surrounding text, a definition, or a condition when the reader needs it, with its location and version. Label an editorial summary as a summary; it cannot replace the actual passages. Choose context by the dependency, not a fixed number of neighboring sentences. If necessary context is missing, say what remains unverified. Reuse shared context by reference rather than repeating it in every unit.
2. **Before.** Give the original location and actual passage, including relevant formulas.
3. **After.** Give the revised location and corresponding actual passage. For additions or deletions, explicitly state that the other side has no counterpart and show the insertion or deletion context.
4. **Explanation.** Name what changed and explain how it affects the passage, using specific quantities, conditions, or referents. Distinguish author-provided reasons, editor-proposed reasons, inferred benefits, and unknown intent. A supplied reason may still conflict with the text. Avoid generic explanations such as "more academic."
5. **Meaning and review status.** Identify exposition-only, equivalent, substantive, or uncertain changes. State what was checked and what was not. A claim of mathematical equivalence needs an actual justification; identical tokens or successful compilation do not establish it.

For routine language fixes, keep the explanation and review status brief. Group nearby fixes when they belong to one coherent passage; do not turn each punctuation mark into a review form.

Use section names and faithfully quoted anchors; add file names, paragraph IDs, occurrence numbers, or source lines when reliable. A line number alone is fragile. If repeated text prevents a unique mapping, mark the ambiguity instead of inventing a precise correspondence.

Account for changes across the selected scope, including deleted material and added text. Represent a split or merge as one unit with multiple before or after passages; a move may also contain a rewrite. Displaying these relationships does not guarantee that every change was detected. Report incomplete coverage honestly. When no changes are found, say so; do not manufacture edits.

## Highlight and check

Use passage-level annotations by default. Use word-level highlighting only where alignment has been checked. Keep unchanged text black. In color output, use blue `#005587` for added text, purple `#742F75` for rewritten text, and muted green `#416748` for movement, reformatting, and notes. Pair colors with explicit labels and IDs. In Markdown, labels and headings carry the meaning; do not rely on client-specific color rendering.

Keep a before/after pair together when readable, or on immediately adjacent pages. Stack long prose and equations; use columns only when both sides remain legible. A pure move can display the passage once with both locations. Do not obscure formulas with deletion marks or shorten them to fit the layout.

Check each changed unit with the context needed to interpret it: definitions, conditions, referents, claim strength, citation attachment, comparators, and mathematical details. Explain substantive or uncertain changes even when comparing user-supplied versions. This is a scoped review of changes, not a full proof, citation, or scientific audit.

Verify that quotations match the snapshots, locations resolve, the proposed text matches the authoritative revision, and each listed change has an appropriate counterpart or an explicit absence. Check for changes omitted from the index. Recheck input hashes before delivery; disclose concurrent changes rather than silently adopting a new baseline.

## Deliver

Honor an explicit format request. Otherwise, prefer PDF with editable TeX and a Markdown companion. Follow the [rendering guide](references/rendering.md) and use the bundled helper to select an existing LaTeX environment and compile the generated comparison within its time and retry limits. Inspect the returned PDF or page previews. If export fails, deliver `comparison.md`, retain useful TeX and diagnostics, and explain the fallback and unperformed checks. Ordinary report generation does not authorize installing LaTeX or adding packages.

Return the primary comparison, snapshot and revised-text locations, coverage, and unresolved issues. A clean revised draft may accompany the comparison; it does not replace the before/after pairs. Keep manuscript text in its language and use the requested language for explanations. English is the default for notes inside an English manuscript.

## Apply only when requested

Apply the selected revision to the authorized target without generating new wording. Re-read the target and the selected revision and compare them with the saved identities before writing; stop and report a mismatch rather than applying a stale proposal. If only some change IDs are selected, check their dependencies and flag conflicts without silently applying additional edits. These checks are not an atomic-write guarantee.

Preserve the baseline through a snapshot or existing version control. Deliver clean text unless annotations were also requested; keep requested annotations switchable and distinguishable from manuscript prose. Applying edits does not authorize a commit, push, or publication.
