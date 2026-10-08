# Grammar edit beside a multiline equation

This synthetic example illustrates a small language correction while preserving the surrounding mathematical setup. The card layout has an editable [LaTeX comparison](comparison-styled.tex), a checked [PDF](comparison-styled.pdf), and a [rendered page preview](comparison-styled-preview.png). The earlier [plain LaTeX comparison](comparison.tex) and [PDF](comparison.pdf) are retained.

- **Mode:** propose-and-compare; language-only, grammar correction.
- **Versions:** [before.tex](before.tex) → [after.tex](after.tex); [identity.json](identity.json) records the compared source bytes.
- **Coverage:** the entire source fragments were compared. The setup, equation, labels, and concluding sentence are unchanged. C1 is the only text edit.
- **Granularity:** sentence-level quotation, with the full unchanged mathematical context below. The PDF colors one checked word replacement.

## Context

Setup, unchanged in both versions:

```tex
Let $X\in\mathbb{R}^{n\times d}$, $y\in\mathbb{R}^{n}$,
$n\geq 1$, and $\lambda>0$. The parameter is $\theta\in\mathbb{R}^d$.
```

**Editor summary:** the passage introduces a regularized least-squares objective. The parameter dimensions and positive regularization condition remain part of the setup.

## C1 · Correct subject–verb agreement

**Before location:** objective-introduction sentence; anchor “We minimizes”.

```tex
We minimizes the following regularized objective:
```

**After location:** the same sentence; anchor “We minimize”.

```tex
We minimize the following regularized objective:
```

**Explanation — editor-proposed:** “We” takes “minimize,” not “minimizes.” The optimization action and objective remain the same.

**Meaning and review:** exposition-only. A byte comparison of the fragments shows that this verb ending is the only change. This verifies preservation of the formula's source, not correctness of a theorem or properties of an unseen implementation.

## Unchanged equation

This is the exact equation block from both snapshots, not a shortened rendering:

```tex
\begin{align}
F(\theta)
 &= \frac{1}{2n}\sum_{i=1}^{n}
    \left(\sum_{j=1}^{d}X_{ij}\theta_j-y_i\right)^2
    +\frac{\lambda}{2}\|\theta\|_2^2 \label{eq:objective}\\
 &= \frac{1}{2n}\|X\theta-y\|_2^2
    +\frac{\lambda}{2}\sum_{j=1}^{d}\theta_j^2. \nonumber
\end{align}
```

## PDF presentation mapping

The wrapper renames `eq:objective` to `before:eq:objective` and `after:eq:objective`, and displays the copies as B1 and A1. These are presentation mappings, not source edits. Both source files retain `eq:objective`. Counters and PDF hyperlink destinations are managed separately from label names.

The inline macro colors the changed verb; it does not wrap the `align` environment. Turning annotations off hides color and notes, but the comparison still contains both versions and is not a clean manuscript.

To rebuild from this directory with a local LaTeX installation:

```sh
mkdir -p ../../.scratch/math-style-build
pdflatex -halt-on-error -interaction=nonstopmode \
  -output-directory=../../.scratch/math-style-build comparison-styled.tex
pdflatex -halt-on-error -interaction=nonstopmode \
  -output-directory=../../.scratch/math-style-build comparison-styled.tex
```

The preview demonstrates this particular wrapper and multiline equation. Arbitrary manuscript packages or display environments may require different handling.
