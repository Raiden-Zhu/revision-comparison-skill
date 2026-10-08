# Language edit: make the operation clear

This synthetic section describes a gate on frozen features. The requested revision clarifies the acting component and shortens one passive construction. It does not change the model or evaluation.

- **Mode:** propose-and-compare; language-only.
- **Versions:** [before.md](before.md) → [after.md](after.md). File identities are recorded in [identity.json](identity.json).
- **Coverage:** both source files were compared. The Method heading and its first paragraph, the document title, and Evaluation are unchanged. C1 and C2 cover the two changed paragraphs.
- **Granularity:** passage-level. Fenced passages are exact source quotations; they carry no word-level diff claim.

## Shared context

Method, paragraph 1, unchanged in both versions:

```markdown
The feature extractor produces $h(x)$ and remains frozen. The gate $g_\theta$ is the only trainable component.
```

**Editor summary:** the extractor computes the features; the trainable gate selects coordinates for the classifier. This context identifies the subject of C1. It also limits C2: the edit must not imply that the extractor is trained.

## Change index

| ID | Operation | Location | Meaning |
| --- | --- | --- | --- |
| [C1](#c1--name-the-acting-component) | Rewritten | Method, paragraph 2 | Exposition-only |
| [C2](#c2--shorten-the-passive-construction) | Rewritten | Method, paragraph 3 | Exposition-only |

## C1 · Name the acting component

**Context:** see the shared definition above. The referent of “It” is recoverable, but naming the gate avoids asking the reader to choose between the two components in the preceding paragraph.

**Before location:** Method, paragraph 2; anchor “It acts on”.

```markdown
It acts on $h(x)$, and it controls which coordinates reach the classifier.
```

**After location:** Method, paragraph 2; anchor “The gate $g_\theta$ acts on”.

```markdown
The gate $g_\theta$ acts on $h(x)$ and controls which coordinates reach the classifier.
```

**Explanation — editor-proposed:** name the gate and remove the repeated subject. This is a clarity edit, not a claim that the original sentence was grammatically invalid.

**Meaning and review:** exposition-only. Checked against the shared definition: the gate, input features, and coordinate-selection role are preserved. No scientific validity audit was performed.

## C2 · Shorten the passive construction

**Before location:** Method, paragraph 3; anchor “The gated features are used”.

```markdown
The gated features are used by the classifier. The extractor is not updated.
```

**After location:** Method, paragraph 3; anchor “The classifier uses”.

```markdown
The classifier uses the gated features. The extractor is not updated.
```

**Explanation — editor-proposed:** the shorter active construction names the same consumer. Passive voice is not inherently an error; this is an optional expression improvement.

**Meaning and review:** exposition-only. The frozen-extractor condition remains verbatim. No formulas, numbers, citations, or evaluation claims were changed.

## Delivery

`after.md` is the sole proposed revision used here. Neither source file is modified by this comparison. There are no unresolved mappings in this small example.
