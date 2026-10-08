# Gated feature model

## Method

The feature extractor produces $h(x)$ and remains frozen. The gate $g_\theta$ is the only trainable component.

It acts on $h(x)$, and it controls which coordinates reach the classifier.

The gated features are used by the classifier. The extractor is not updated.

## Evaluation

We compare the gated model with the same classifier using all frozen features. Both models use the same training and evaluation splits.
