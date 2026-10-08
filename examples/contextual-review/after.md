# Adapting cached features

## Summary

The adapter reduces end-to-end training time by 38%.

## Method

We cache one embedding per image from a frozen encoder and train a small adapter on the cached embeddings.

The baseline is a linear classifier trained on the same cached embeddings.

## Evaluation Protocol

We use one image-classification dataset with a fixed train/test split. The adapter and linear baseline use the same cached embeddings, split, optimizer, and training budget.

We report mean test accuracy and mean optimization time across five seeds. Timing starts after feature precomputation and excludes that cost.

## Results

The adapter reaches 84.2% mean test accuracy, compared with 82.7% for the baseline.
