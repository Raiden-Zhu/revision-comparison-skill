# Rendering comparisons

The comparison should be readable before it is decorative. Keep exact passages, context, and change IDs available in every output format.

## Markdown

Use headings for change IDs and locations, followed by Context, Before, After, and a concise explanation and review note. Fenced blocks preserve source characters when math, markup, or citation syntax would otherwise be interpreted. Unchanged context must be identifiable as context, not another edited passage.

For a long report, link a change index to its headings. Do not put long passages in a wide table or insert color markup into equations. Multiple original or revised passages belong under one ID for a split or merge. State an absent counterpart explicitly.

## LaTeX and PDF

For a new standalone PDF comparison, use the [visual theme](../assets/comparison-style.tex) unless the user supplies another layout. It provides navy headings, light Before/After cards, and green context and reason cards, with the same annotation colors as the core skill. The theme changes presentation only; source text, editing scope, reasons, and verification remain governed by the comparison contract.

Load `annotations.tex`, then `comparison-style.tex`, using paths relative to the wrapper. Use `\rcReportTitle{Title}{Subtitle}`, `rcContext` for context or reason cards, and `\begin{rcPassage}{C1}{BEFORE}{Short location}` for each passage. Keep the third argument short; put longer paths or anchors in the body. Page size and margins belong to the wrapper. The theme uses Latin Modern, `tcolorbox` with its `breakable` and `skins` libraries, and `fancyhdr`, available in common TeX distributions. If packages are unavailable, use a simple readable layout and disclose the fallback.

The cards can break across pages and repeat the change ID and side heading. Keep the original font size for prose and equations; do not make a fixed-height box or shrink content to reproduce a screenshot. Wrap optional reason cards in `\ifrcannotations ... \fi` when they should follow the annotation switch. The [language example](https://github.com/Raiden-Zhu/revision-comparison-skill/blob/main/examples/language-edit/comparison-readable.tex) and [mathematical example](https://github.com/Raiden-Zhu/revision-comparison-skill/blob/main/examples/math/comparison-styled-readable.tex) are complete editable wrappers.

The optional [annotation macros](../assets/annotations.tex) provide text colors and switchable notes, not a diff engine or document renderer. Use `\rcadd{...}` and `\rcrewrite{...}` for ordinary inline text or short inline math. Do not wrap arbitrary paragraphs, display math, `align`, verbatim content, or fragile commands in these macros. Use labels and notes around complex blocks instead.

Build a standalone wrapper with the source packages and definitions actually needed. Prefix labels with names such as `before:...` and `after:...`. Manage equation counters and hyperlink destinations separately, and use separate bibliography contexts if the versions have conflicting citation keys or entries. Record any renamed labels as presentation mappings; preserve the equations and their conditions. For an unresolved external reference, show its source label or number when known and state that it has not been resolved. A readable label is not verification of the reference's meaning or support.

Use stacked blocks for long passages. Let them break across pages; avoid an unbreakable box that clips content. Repeat the change ID and side heading when a pair spans pages. Never abbreviate formulas or reduce them to an unreadable size to force a pair onto one page.

Fix compilation problems in the wrapper, not in supplied before/after text. If the source itself is broken, quote it faithfully in a safe block and report the problem. Keep raw snapshots available when escaping or label isolation changes the displayed source representation.

Compile with the available LaTeX toolchain and check errors, unresolved references, clipping, and overfull boxes. Inspect the pages containing changed passages, long formulas, and representative original material. A successful build alone is not a visual check. A breakable outer card does not guarantee that every display environment can split; handle long mathematics without altering or omitting its source. The repository examples demonstrate checked layouts, not support for every manuscript preamble.

## Clean and annotated outputs

Switching off annotation macros hides colors and notes in an annotated revised manuscript. It does not turn a comparison document into a clean manuscript: the comparison still contains the original passages. Build any clean manuscript from the same authoritative revision, without rewriting during export.

## Other formats

Use a host's native document tools when available and requested. This repository does not supply a DOCX tracked-changes adapter or an interactive HTML application. Report the actual export and validation performed instead of claiming a format is supported merely because a host might offer it.
