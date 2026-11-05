# Behavioral checks

Use these cases when changing the skill. Give an independent agent the installed skill, a realistic request, and only the raw inputs it needs. Inspect what it actually produces. Keep generated test artifacts in an isolated directory, outside published examples.

Formatting checks do not establish good editing decisions. The checks below concern observable behavior and traceability, not a fixed set of headings or an exact preferred sentence.

| Case | Request and input | What to inspect |
| --- | --- | --- |
| Existing versions | Compare two drafts; the revised version still has a grammar error and changes a result value. | Both supplied texts stay faithful. The report identifies the value change, preserves the error, and does not invent a third draft or an author motive. |
| Grammar-only proposal | Correct agreement in a draft containing a proof claim; no proof is provided. | The grammatical defect is fixed in one authoritative proposal. The proof claim and conditions are preserved; lack of proof is not treated as evidence that it is false. |
| No changes | Compare identical files, then a pair differing only in layout. | Identical inputs yield no invented changes. Formatting changes are not classified as scientific revisions. |
| Meaning changes | Remove a condition and change a number, quantifier, or inequality. | Each difference appears in a located unit. Substantive changes are not called cosmetic, and noticing a difference is not confused with proving the revised claim false. |
| Context and correspondence | Move and rewrite a paragraph; split or merge others; repeat an anchor in two sections. | Necessary definitions and conditions are sourced, summaries are labeled, ambiguous mappings are disclosed, and deletions are not lost. Context may come from outside the selected editing scope. |
| Math and references | Compare multiline equations and an external reference; export the comparison as PDF. | Equations and conditions are preserved, labels and counters are handled separately, unavailable references are disclosed, and rendered pages have no clipping or obscured content. |
| Default output | Compare two short versions without naming an output format; a working LaTeX environment is available. | The agent checks or reuses the existing toolchain, delivers a compiled PDF with editable TeX and a Markdown companion, and checks the rendered report. It does not install software. |
| Unavailable PDF environment | Request a comparison without naming a format; the available toolchain check fails. | A complete Markdown comparison is delivered with the concrete fallback reason. Useful TeX or diagnostics are retained if created; no installation or fabricated PDF success is reported. |
| Explicit Markdown | Request a Markdown-only comparison despite an available LaTeX environment. | The requested Markdown is delivered without PDF preflight, compilation, or dependency installation. |
| Alternate compiler | Put an unusable or crashing compiler before a working installation. | The bounded helper tries the next suitable candidate, without changing either installation; it stops after at most three candidates. |
| Bounded export | Stall a child process or resubmit a wrapper after failed repairs. | Only that task's process tree is stopped; automatic execution shares one budget across calls, and at most two further calls are allowed. The completed Markdown remains available. |
| Private setup | Existing TeX is missing packages and optional setup is requested. | Only installer-marked private TinyTeX may receive packages. System TeX, unrelated user trees, and unmarked directories are preserved. |
| Rationale conflict | Supply a reason saying “formatting only,” but change a formula or result. | The supplied reason is attributed and its conflict with the actual change is reported. Supplied does not automatically mean verified. |
| Partial or stale application | Select dependent changes, or change the source/proposal after review. | The agent checks the selected version and target, reports drift or dependency conflicts, and does not silently regenerate wording or apply extra changes. No atomic-write guarantee is inferred. |

## Small raw fixtures

For an existing-version comparison, use:

```markdown
## Result

Under bounded variance, the estimator converges.

The model reach 0.81 accuracy.
```

and:

```markdown
## Result

The estimator converges.

The model reach 0.84 accuracy.
```

Request a separate comparison of the supplied versions. Do not ask for a rewrite. Check the condition deletion and value change, and confirm that “model reach” survives in the quoted supplied text.

For a grammar-only proposal, use:

```markdown
## Method

We prove consistency under bounded variance.

The estimators is evaluated on the held-out split.
```

Request grammar and punctuation correction only, followed by a separate comparison. The missing proof does not authorize changing “prove” to “suggest.”

The [published examples](../examples) cover language, structural correspondence, semantic risks, and a multiline equation. Their saved identities make the compared versions explicit. They are illustrations, not a measured benchmark or a guarantee that the skill detects every change in a manuscript.
