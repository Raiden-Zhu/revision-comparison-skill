# Structural edit: separate setup, training, and reporting

This synthetic protocol describes a fixed split, a frozen extractor, the gate's training budget, and the reported metric. The requested structural edit makes those roles easier to find and removes a repeated condition. It adds no experimental result or new procedure.

- **Mode:** propose-and-compare; structural editing of this short document.
- **Versions:** [before.md](before.md) → [after.md](after.md); identities in [identity.json](identity.json).
- **Coverage:** the title and existing headings are retained. C1–C5 account for all paragraph and heading changes; the unchanged training sentence is shown once as a move.
- **Granularity:** passage-level, including a heading-level addition.

## Context

**Editor summary:** Protocol describes the fixed split and frozen extractor, Training gives the update count, and Reporting describes test accuracy and its five-seed average.

## Change index

| ID | Operation | Before → After | Meaning |
| --- | --- | --- | --- |
| [C1](#c1--split-the-setup-paragraph) | Split | Protocol ¶1 → Protocol ¶1–2 | Exposition-only |
| [C2](#c2--remove-the-repeated-condition) | Deleted | Reporting ¶1 → no counterpart | Exposition-only |
| [C3](#c3--combine-metric-and-aggregation) | Merged + Rewritten | Reporting ¶2–3 → Reporting ¶1 | Equivalent, within the stated context |
| [C4](#c4--add-a-training-heading) | Added | no counterpart → Training heading | Exposition-only |
| [C5](#c5--move-the-training-sentence) | Moved | Protocol ¶2 → Training ¶1 | Exposition-only |

## C1 · Split the setup paragraph

**Before location:** Protocol, paragraph 1; anchor “We use a fixed training split.”.

```markdown
We use a fixed training split. The feature extractor is frozen in both conditions.
```

**After locations:** Protocol, paragraphs 1 and 2.

Paragraph 1:

```markdown
We use a fixed training split.
```

Paragraph 2:

```markdown
The feature extractor is frozen in both conditions.
```

**Explanation — editor-proposed:** give the fixed-split condition and the frozen-extractor condition separate paragraphs.

**Meaning and review:** exposition-only. Both sentences and their order are preserved exactly. No condition is dropped.

## C2 · Remove the repeated condition

**Before location:** Reporting, paragraph 1; anchor “The training split is kept fixed.”.

```markdown
The training split is kept fixed.
```

**After:** no corresponding paragraph. In the revised document, Reporting opens with the metric sentence shown in C3.

**Context:** the unchanged condition “We use a fixed training split.” remains in Protocol, as shown in C1. The deletion therefore removes a repetition rather than the only statement of the condition.

**Explanation — editor-proposed:** keep the shared split in setup and let Reporting focus on the outputs.

**Meaning and review:** exposition-only within this document. The condition is still present. This judgment would need revisiting if Reporting were exported as a standalone unit.

## C3 · Combine metric and aggregation

**Before locations:** Reporting, paragraphs 2 and 3.

Paragraph 2:

```markdown
We record test accuracy.
```

Paragraph 3:

```markdown
We report the average across five seeds.
```

**After location:** Reporting, paragraph 1; anchor “We record test accuracy and report”.

```markdown
We record test accuracy and report the average across five seeds.
```

**Explanation — editor-proposed:** put test accuracy and its five-seed average in one sentence.

**Meaning and review:** equivalent within the supplied context: test accuracy is the only metric named, and the average still covers five seeds. If the preceding text named several metrics, check which one the average refers to.

## C4 · Add a Training heading

**Before:** no heading counterpart. Insertion context: the last setup sentence is followed by the existing training-budget paragraph.

**After location:** between Protocol and Reporting.

```markdown
## Training
```

**Explanation — editor-proposed:** name the existing training step. The added heading introduces no new procedure.

**Meaning and review:** exposition-only. Review with C5: the heading's purpose depends on the paragraph placed beneath it.

## C5 · Move the training sentence

**From:** original Protocol, paragraph 2. **To:** revised Training, paragraph 1. The content is unchanged and is shown once:

```markdown
We train the gate for 2,000 updates.
```

**Explanation — editor-proposed:** place the existing update budget under the new heading.

**Meaning and review:** exposition-only. The update count and trained component are unchanged. C4 and C5 form a coherent structural edit; selecting only one may leave an empty heading or undo the intended organization.

## Delivery

The comparison preserves the exact source passages. `after.md` is the sole proposed revision; it has not been applied. This example checks changes to the text, with no experimental records supplied.
