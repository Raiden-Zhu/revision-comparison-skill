# Contextual review: the number stays, the claim changes

This synthetic excerpt describes an adapter trained on cached features from a frozen encoder. The supplied revision makes the method more concise, moves the reporting protocol, and changes the scope of the timing claim. The comparison explains all three changes; it preserves the supplied revision, including the claim that needs author review.

The [PDF](comparison.pdf) uses the same card theme as the homepage. Its [editable LaTeX](comparison.tex) and [first-page preview](comparison-preview.png) are included. The [homepage excerpt](comparison-detail.png) is rendered directly from the first PDF page.

- **Mode:** compare; both versions are supplied. No author brief or explanation accompanies them.
- **Versions:** [before.md](before.md) → [after.md](after.md); byte identities in [identity.json](identity.json).
- **Scope and coverage:** both complete source files. C1 covers Method paragraph 1; C2 covers the two reporting paragraphs moved from Results into Evaluation Protocol; C3 covers Summary paragraph 1. The title, headings, baseline definition, evaluation setup, and accuracy result are retained.
- **Granularity:** passage-level for C1/C2. C3's highlighted replacement is exactly `optimization` → `end-to-end training`; the remaining words are unchanged.
- **Limits:** this is a comparison of synthetic text. No experimental records are supplied; measurement validity, significance, and real-world performance are not verified. There are no formulas, citations, or external source dependencies.

## Change index

| ID | Operation | Before → After | Meaning and review |
| --- | --- | --- | --- |
| [C1](#c1--make-the-training-description-more-concise) | Rewritten | Method ¶1 → Method ¶1 | Exposition-only; stated operations preserved |
| [C2](#c2--move-and-merge-the-reporting-protocol) | Moved and merged | Results ¶2–3 → Evaluation Protocol ¶2 | Reporting scope and timing boundary preserved |
| [C3](#c3--broaden-the-timing-claim) | Rewritten | Summary ¶1 → Summary ¶1 | Substantive scope change; author review needed |

Paragraph numbers count prose blocks under each heading, separately in each version. C3 appears first because its interpretation depends on the protocol moved by C2.

## C3 · Broaden the timing claim

**Editorial role:** the Summary states the headline timing result. To assess this edit, the reader needs the measurement boundary from a different section.

**Source context:** After, Evaluation Protocol ¶2, sentence 2; retained verbatim from Before, Results ¶3, sentence 2:

```markdown
Timing starts after feature precomputation and excludes that cost.
```

The shared evaluation setup identifies the comparison. Evaluation Protocol ¶1, unchanged in both versions:

```markdown
We use one image-classification dataset with a fixed train/test split. The adapter and linear baseline use the same cached embeddings, split, optimizer, and training budget.
```

**Before location:** Summary ¶1; anchor “The adapter reduces optimization time”.

```markdown
The adapter reduces optimization time by 38%.
```

**After location:** Summary ¶1; anchor “The adapter reduces end-to-end training time”.

```markdown
The adapter reduces end-to-end training time by 38%.
```

**Observed change:** `optimization` is replaced with `end-to-end training`; `38%` is retained. The metric's stated scope expands even though its value does not change.

**Explanation — inferred; author intent unknown:** the revised wording reads as a broader timing claim. The supplied protocol excludes feature precomputation, so it does not substantiate end-to-end time. Whether the author intended a new metric or has additional measurements is unknown.

**Meaning and review:** substantive scope change; author review needed. The mismatch between the revised wording and the supplied timing boundary is checked. The report does not establish that the number is false or independently verify either measurement. It does not repair the supplied After text.

**Connection to C2:** the timing boundary was moved, not deleted. Its After location supplies the context for this judgment.

## C1 · Make the training description more concise

**Before location:** Method ¶1; anchor “We keep the encoder fixed”.

```markdown
We keep the encoder fixed. We compute one embedding per image and store it. A small adapter is trained on these stored embeddings.
```

**After location:** Method ¶1; anchor “We cache one embedding per image”.

```markdown
We cache one embedding per image from a frozen encoder and train a small adapter on the cached embeddings.
```

**Explanation — inferred benefit; author intent unknown:** one sentence joins feature computation, storage, and adapter training. “Frozen encoder” retains the fixed-encoder condition; “cache” names the storage step directly. The original wording is grammatical.

**Meaning and review:** exposition-only. The fixed encoder, one embedding per image, storage, and adapter training on those embeddings are preserved in the stated description. No mechanism, equation, or experiment is independently verified.

## C2 · Move and merge the reporting protocol

**Before location 1:** Results ¶2; anchor “We report mean test accuracy”.

```markdown
We report mean test accuracy across five seeds.
```

**Before location 2:** Results ¶3; anchor “We report mean optimization time”.

```markdown
We report mean optimization time across five seeds. Timing starts after feature precomputation and excludes that cost.
```

**After location:** Evaluation Protocol ¶2; anchor “We report mean test accuracy and mean optimization time”.

```markdown
We report mean test accuracy and mean optimization time across five seeds. Timing starts after feature precomputation and excludes that cost.
```

**Explanation — inferred benefit; author intent unknown:** the two reporting statements are combined and placed before the accuracy result. The reader meets the metrics, seed aggregation, and timing boundary together in the protocol.

**Meaning and review:** equivalent reporting description within this excerpt. Both metrics still use five-seed means, and the timing boundary is unchanged. This is a move with a merge, not two deletions followed by an unrelated addition. The accuracy result remains verbatim.

## Delivery

Both supplied versions remain authoritative snapshots; no third version or applied edit is produced. All changed passages in this short excerpt map to C1–C3; no mapping is unresolved. C1 and C2 illustrate helpful wording and organization, while C3 records a scope change that needs author review. Input hashes identify the files and do not certify the underlying research.
