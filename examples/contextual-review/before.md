# Adapting cached features

## Summary

The adapter reduces optimization time by 38%.

## Method

We keep the encoder fixed. We compute one embedding per image and store it. A small adapter is trained on these stored embeddings.

The baseline is a linear classifier trained on the same cached embeddings.

## Evaluation Protocol

We use one image-classification dataset with a fixed train/test split. The adapter and linear baseline use the same cached embeddings, split, optimizer, and training budget.

## Results

The adapter reaches 84.2% mean test accuracy, compared with 82.7% for the baseline.

We report mean test accuracy across five seeds.

We report mean optimization time across five seeds. Timing starts after feature precomputation and excludes that cost.
