# Contextual review: the number stays, the claim changes

This synthetic excerpt describes an adapter trained on cached features from a frozen encoder. The supplied revision makes the method more concise, moves the reporting protocol, and changes the scope of the timing claim. The comparison explains all three changes; it preserves the supplied revision, including the claim that needs author review.

The [PDF](comparison-readable.pdf) uses the same card theme as the homepage. Its [editable LaTeX](comparison-readable.tex) and [first-page preview](comparison-readable-preview.png) are included. The [homepage excerpt](comparison-readable-detail.png) is rendered directly from the first PDF page.

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

**Editorial role:** the Summary states the main timing result. To read this edit, check what the timer includes in the Evaluation Protocol.

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

**Explanation — inferred:** the reported 38% reduction is for optimization time only: feature precomputation is excluded. The revision calls this an end-to-end reduction. No author explanation was supplied.

**Meaning and review:** substantive scope change; author review needed. The wording was checked against both drafts; the underlying timings remain unverified. Check which timing measurement the 38% refers to.

**Connection to C2:** the timing definition still appears in the revised draft, now in Evaluation Protocol. Read it alongside the changed Summary sentence.

## C1 · Make the training description more concise

**Before location:** Method ¶1; anchor “We keep the encoder fixed”.

```markdown
We keep the encoder fixed. We compute one embedding per image and store it. A small adapter is trained on these stored embeddings.
```

**After location:** Method ¶1; anchor “We cache one embedding per image”.

```markdown
We cache one embedding per image from a frozen encoder and train a small adapter on the cached embeddings.
```

**Explanation — inferred benefit:** the revision describes caching the features and training the adapter in one sentence. “Frozen encoder” keeps the fixed-encoder condition, and “cache” includes storing the embeddings. The original wording is grammatical.

**Meaning and review:** exposition-only. Both descriptions keep the encoder fixed, store one embedding per image, and train the adapter on those embeddings.

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

**Explanation — inferred benefit:** the two reporting statements now appear together before the accuracy result. Readers can find both metrics, the five-seed averages, and what the timer includes in one place.

**Meaning and review:** equivalent within this excerpt. Both metrics still use five-seed means, and feature precomputation is still excluded from timing. The two source paragraphs form the revised reporting paragraph. The accuracy result is unchanged.

## Delivery

Both supplied drafts are preserved. C1–C3 account for all changed passages in this excerpt, with no unresolved mappings. C1 and C2 improve wording and organization; C3 needs author review because the timing claim has changed. File hashes are recorded in `identity.json`.
