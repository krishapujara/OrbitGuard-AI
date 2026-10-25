# Model Card ? `below_threshold_proxy` Classification Baseline

| Specification Item | Details |
| :--- | :--- |
| **Model Architecture** | `Pipeline(steps=[('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler()), ('clf', LogisticRegression(class_weight='balanced', random_state=42))])` |
| **Primary Artifact** | `ml/artifacts/baseline_model.joblib` and metadata `baseline_model.meta.json` |
| **Synchronized Artifact** | `models/artifacts/baseline_model.joblib` and `baseline_model.meta.json` |
| **Origin Security Gate** | `trusted_origin == 'orbitalguard-ai-local'` strictly required by `ModelPredictionService` |
| **Target Variable** | `below_threshold_proxy`: Binary label ($1$ if refined SGP4 miss distance $\le$ threshold, $0$ otherwise) |
| **Explicit Non-Target** | Real-world spacecraft collision, operational collision probability ($P_c$), or certified risk standard |
| **Predictive Features** | `backend.feature_engineering.FEATURE_COLUMNS` strictly available at prediction epoch $t_0$ |
| **Validation Strategy** | Grouped chronological holdout on `candidate_id` with canonical pair deduplication `canonical_pair_id` |
| **Baselines Compared** | Dummy Most-Frequent Classifier and Physical Epoch-Threshold Baseline ($d(t_0) \le \text{threshold}$) |

---

## 1. Dataset & Split Methodology

- **Source Dataset:** Processed proxy dataset `data/processed/proxy_dataset.csv` generated from CelesTrak GP orbital elements (`visual` group snapshot).
- **Total Dataset Size:** 177 unique, deduplicated orbital pairs (0 reverse pairs).
- **Partitioning:** Grouped chronological holdout partitioner (`ml/validation.py`):
  - **Train partition:** 105 pairs (36 candidate groups)
  - **Validation partition:** 36 pairs (12 candidate groups)
  - **Test partition:** 36 pairs (12 candidate groups)
- **Zero Leakage:** Candidate IDs and canonical pair IDs appearing in the test partition never appear in training or validation. Imputation and scaling statistics are fitted strictly on the training partition.

---

## 2. Recomputed Evaluation Metrics (Test Partition, $N = 36$)

| Metric | Logistic Regression | Physical Baseline ($d(t_0) \le \text{threshold}$) | Dummy Majority |
| :--- | :---: | :---: | :---: |
| **Accuracy** | **58.33%** | 41.67% | 41.67% |
| **Precision** | **63.64%** | 50.00% | 0.00% |
| **Recall** | **66.67%** | 4.76% | 0.00% |
| **F1-Score** | **0.651** | **0.087** | **0.000** |
| **PR-AUC** | **0.649** | N/A | N/A |
| **ROC-AUC** | **0.613** | N/A | N/A |
| **Brier Score** | **0.249** | N/A | N/A |
| **Log Loss** | **0.739** | N/A | N/A |

### Confusion Matrix (Logistic Regression on Test Set):
```
Predicted Negative (0)   Predicted Positive (1)
       [  7  ]                  [  8  ]        Actual Negative (0)
       [  7  ]                  [ 14  ]        Actual Positive (1)
```

---

## 3. Known Scientific & Practical Limitations

1. **Proxy Approximation**: The model is trained on SGP4 refined outputs of the same catalog snapshot; it approximates geometric close-approach screening rather than predicting true physical collisions.
2. **Single-Snapshot Limitation**: Because the source dataset is derived from a single catalog snapshot, all satellite epochs originate from the same day (`unique_group_epochs == 1`). While grouped splitting prevents identity memorization, the dataset does not represent a true future multi-year operational test.
3. **Uncalibrated Probability**: Predicted model scores (`ml_proxy_score`) are proxy decision scores, not operational collision probabilities ($P_c$).
4. **Safety Disclaimer**: This model must NEVER be used for automated collision-avoidance maneuver planning or life-critical spaceflight safety decisions.
