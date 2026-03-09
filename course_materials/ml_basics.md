# Machine Learning: Basics — Tutor Reference

## Core Concepts

**Machine learning**: A field of computer science where algorithms learn patterns from data to make predictions or decisions without being explicitly programmed for each case.

**Supervised learning**: Learning from labeled data (input-output pairs). The model learns a mapping from inputs X to outputs Y. Subtypes: classification (discrete output: spam/not spam) and regression (continuous output: house price).

**Unsupervised learning**: Learning from unlabeled data. The model discovers structure, groupings, or patterns. Examples: clustering (k-means, DBSCAN), dimensionality reduction (PCA), anomaly detection.

**Semi-supervised learning**: Uses a small amount of labeled data combined with a large amount of unlabeled data. Useful when labeling is expensive.

**Reinforcement learning**: An agent learns by interacting with an environment, receiving rewards or penalties. Not supervised or unsupervised — the agent discovers good strategies through trial and error.

**Features**: The input variables (attributes) used by the model. Feature engineering — selecting, transforming, and creating features — is often more impactful than algorithm choice.

**Labels/targets**: The output variable the model tries to predict in supervised learning.

**Bias-variance tradeoff**: A fundamental tension in model complexity.
- **Bias**: Error from overly simplistic model assumptions. High bias leads to underfitting (model too simple to capture patterns).
- **Variance**: Error from sensitivity to training data fluctuations. High variance leads to overfitting (model memorizes training data noise).
- Ideal models balance both: complex enough to capture true patterns, simple enough to generalize.

**Overfitting**: Model performs well on training data but poorly on unseen data. The model has memorized noise rather than learned the underlying pattern. Signs: large gap between training and validation accuracy.

**Underfitting**: Model performs poorly on both training and test data. The model is too simple to capture the underlying pattern. Signs: low accuracy on everything.

**Train/test split**: Dividing data into a training set (typically 70-80%) for learning and a test set (20-30%) for evaluation. The test set must never be used during training.

**Validation set**: A third split used for hyperparameter tuning and model selection. Prevents "implicit" overfitting to the test set through repeated evaluation.

**Cross-validation**: K-fold cross-validation splits data into k folds, trains on k-1 and validates on 1, rotating through all folds. Provides more robust performance estimates than a single split.

## Key Procedures

- Split data BEFORE any preprocessing that uses statistics from the data (e.g., scaling, imputation).
- Evaluate on test set only once, at the very end.
- Use cross-validation for model selection and hyperparameter tuning.
- Monitor learning curves: plot training and validation error vs training set size or epochs.

## Common Student Misconceptions and Errors

1. **Evaluating on training data**: Students train a model and report its accuracy on the same data used for training. This inflates performance and masks overfitting. They do not understand why a separate test set is necessary.

2. **Confusing supervised and unsupervised**: Students think clustering is supervised because they specify the number of clusters (k). They do not distinguish between providing labels (supervised) and providing parameters (unsupervised).

3. **Thinking more complex models are always better**: Students believe that adding more parameters, layers, or features always improves performance. They do not grasp that complexity beyond the data's true pattern increases variance and leads to overfitting.

4. **Misunderstanding the bias-variance tradeoff**: Students think bias and variance can both be minimized simultaneously without constraint. They do not understand the tradeoff: reducing one typically increases the other for a fixed amount of data.

5. **Data leakage**: Students preprocess the entire dataset (e.g., normalize, compute mean/std) before splitting into train and test. Information from the test set "leaks" into training, inflating performance estimates.

6. **Confusing classification and regression**: Students apply a classification algorithm to a regression problem or vice versa. Example: using linear regression for a binary yes/no prediction without a threshold or logistic function.

7. **Thinking accuracy is always the right metric**: Students report accuracy on imbalanced datasets (e.g., 99% negative class) without realizing that a "predict all negative" model would score 99%. Precision, recall, F1, and AUC are often more informative.

8. **Overfitting to the test set**: Students repeatedly evaluate and tune on the test set, effectively training on it. The test set should be used exactly once for final evaluation.

9. **Ignoring feature scaling**: Students use algorithms sensitive to scale (SVM, k-NN, gradient descent) without normalizing features, leading to features with larger ranges dominating.

10. **Assuming correlation implies predictive power**: Students include correlated features assuming they will help the model, not understanding multicollinearity or spurious correlation.

## Diagnostic Questions

- "If your model gets 98% accuracy on training data but 60% on test data, what does that tell you?" (surfaces overfitting understanding)
- "Why can't you use the same data for training and testing?" (surfaces evaluation misconception)
- "What's the difference between supervised and unsupervised learning? Can you give an example of each?" (surfaces categorical confusion)
- "If you make your model more complex, will it always perform better on new data?" (surfaces bias-variance understanding)
- "When should you compute the mean and standard deviation for normalization — before or after splitting the data?" (surfaces data leakage)
- "Your dataset has 95% negative and 5% positive examples. Is 95% accuracy good?" (surfaces accuracy trap)
- "What would a learning curve look like for an overfitting model?" (surfaces conceptual understanding)

## Worked Example: Common Error and Correct Approach

**Problem**: A student trains a decision tree on 1000 samples and reports 99% accuracy.

**Common incorrect approach**:
Student trains the model on all 1000 samples, then predicts on those same 1000 samples, and reports 99% accuracy. They conclude the model works well.

**Why this is wrong**: Decision trees can perfectly memorize training data (achieving 100% training accuracy). The 99% accuracy reflects memorization, not generalization. On unseen data, the model likely performs much worse.

**Correct approach**:
1. Split data: 800 training, 200 test (never look at test data during training).
2. Optionally use 5-fold cross-validation on the 800 training samples to tune hyperparameters (max_depth, min_samples_leaf).
3. Train final model on all 800 training samples with best hyperparameters.
4. Evaluate once on the 200 test samples. Report this accuracy.
5. If training accuracy is 99% but test accuracy is 70%, the model is overfitting. Reduce complexity (prune the tree, limit depth).

**Tutoring note**: Ask the student to imagine studying only the answer key for an exam, then being tested on those exact same questions. Of course they would score well — but it does not mean they understand the material. The test set is like a new exam they have never seen.
