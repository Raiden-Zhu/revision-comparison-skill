# Existing revision: conditions, movement, and a changed result

This is a synthetic comparison of two supplied drafts. No loss definition, proof, or experiment log accompanies them. The task is to show the differences and identify what would need checking, not to repair the revised draft.

- **Mode:** compare.
- **Versions:** [before.md](before.md) → [after.md](after.md); see [identity.json](identity.json) for file hashes.
- **Scope:** Setup, Result, and Evaluation. The title and all three headings are retained.
- **Coverage:** the units below account for all changed or moved paragraphs in this example; there are no unresolved mappings.
- **Granularity:** passage-level; no claim of verified mathematical equivalence.

## Context

The original Setup states:

```markdown
Assume bounded feature norms and set $\lambda > 0$. We use the regularized estimator defined below.
```

**Editor summary:** the positive regularization parameter is relevant to the original uniqueness statement in C3. The revised draft removes that condition from both places. The estimator and loss are not defined in the supplied material, so neither version's convexity claim can be certified here.

## Change index

| ID | Operation | Before → After | Meaning |
| --- | --- | --- | --- |
| [C1](#c1--remove-the-parameter-condition) | Rewritten; condition removed | Setup ¶1 → Setup ¶1 | Substantive |
| [C2](#c2--move-and-combine-the-objective-description) | Moved + Rewritten | Result ¶2 → Setup ¶2 | Uncertain |
| [C3](#c3--remove-the-condition-from-the-result) | Rewritten; condition removed | Result ¶1 → Result ¶1 | Substantive |
| [C4](#c4--change-the-reported-accuracy) | Rewritten | Evaluation ¶1 → Evaluation ¶1 | Substantive |

## C1 · Remove the parameter condition

**Before location:** Setup, paragraph 1; anchor “Assume bounded feature norms and set”.

```markdown
Assume bounded feature norms and set $\lambda > 0$. We use the regularized estimator defined below.
```

**After location:** Setup, paragraph 1; anchor “Assume bounded feature norms.”.

```markdown
Assume bounded feature norms. We use the regularized estimator defined below.
```

**Explanation — observed change; intent unknown:** the revised setup drops the positive-parameter condition. No author reason was supplied.

**Meaning and review:** substantive. The removal is directly checked against the quotations. Whether the broader setup is justified is unverified. Do not describe this as merely shortening a sentence.

## C2 · Move and combine the objective description

**Passage role — editor-assigned:** introduce the objective before discussing its properties.

**Before location:** Result, paragraph 2; anchor “We minimize the sum”.

```markdown
We minimize the sum of the empirical loss and the quadratic penalty. The penalty term is weighted by $\lambda$.
```

**After location:** Setup, paragraph 2; anchor “The objective combines”.

```markdown
The objective combines the empirical loss with a quadratic penalty weighted by $\lambda$.
```

**Explanation — inferred benefit:** moving this description may prepare the reader for the Result. The two sentences become one; no author explanation was supplied.

**Meaning and review:** uncertain. The same two terms and penalty weight remain, but “combines” no longer states the additive form or the minimization action explicitly. Check whether the missing formula and surrounding method recover these details; do not infer equivalence from shared terminology. The separate removal of $\lambda > 0$ belongs to C1 and C3.

## C3 · Remove the condition from the result

**Context:** C1 shows that Setup no longer supplies the condition either. Reading the Result in isolation would miss this second removal.

**Before location:** Result, paragraph 1; anchor “When $\lambda > 0$”.

```markdown
When $\lambda > 0$, the objective is strongly convex and has a unique minimizer.
```

**After location:** Result, paragraph 1; anchor “The objective is strongly convex”.

```markdown
The objective is strongly convex and has a unique minimizer.
```

**Explanation — observed change; intent unknown:** the revised statement is unconditional with respect to $\lambda$ within the supplied text. Its correctness cannot be inferred from smoother wording.

**Meaning and review:** substantive. No proof or loss assumptions were provided. Flag the broader claim for verification; do not silently reinsert the condition into the supplied `after.md` or declare the original theorem proved.

## C4 · Change the reported accuracy

**Before location:** Evaluation, paragraph 1; anchor “The estimator reaches 0.81”.

```markdown
The estimator reaches 0.81 accuracy on the held-out split.
```

**After location:** Evaluation, paragraph 1; anchor “The estimator reaches 0.84”.

```markdown
The estimator reaches 0.84 accuracy on the held-out split.
```

**Explanation — observed change; intent unknown:** the reported value increases by 0.03. The split description is unchanged.

**Meaning and review:** substantive, supporting evidence unavailable. The textual difference is verified; the new measurement is not. Neither value should be treated as a real experimental result outside this synthetic example.

## Unresolved issues

- Check the loss assumptions and the intended range of $\lambda$ before accepting C1 and C3.
- Verify C4 against the actual evaluation record.
- C1 and C3 are related. Selecting one for application requires reviewing the other and the surrounding assumptions; approval of one ID does not automatically authorize the other.

The two supplied drafts remain unchanged. No corrected third draft is produced.
