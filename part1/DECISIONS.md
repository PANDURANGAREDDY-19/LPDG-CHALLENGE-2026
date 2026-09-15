# Part 1 — Decision Log

## 1. Expanded Feature Set for Anomaly Detection
The company's baseline uses only three features (`offline_duration_sec`, `disconnection_cnt`, `reboot_cnt`) per gateway to detect anomalies. I extended this to use all informative features from the dataset, as limiting to three features risks missing anomalies that manifest in other signals such as traffic, signal quality, or system load.

## 2. Feature Selection via Variance and Correlation Thresholds
To avoid noise and redundancy while retaining maximum signal, features were filtered in two stages:
- **Variance Threshold (≤ 0.01)** — removes near-constant features that carry no discriminative information.
- **Correlation Threshold (> 0.95)** — removes one of any highly correlated pair, keeping the feature with fewer missing or invalid values.
This reduced the dataset from the full column set to 42 meaningful features.

The dropped colums are:
```bash 
reboot_importance
operator_unknown
operator_3AT
operator_A1
operator_Eplus
operator_OrangeLU
operator_Salt
operator_Swisscom
operator_TmobileA
```
Where Upon Observing the Data all Operator based Columns that are removed have 0 Standard Deviation and Variance

## 3. Retained the Baseline SIGMA Value of 3.0
The company's baseline uses a fixed sigma of 3.0. I retained this value as there is no labelled evaluation data available to tune or validate an alternative threshold. Changing it without a ground truth to measure against risks either increasing false positives (lower sigma) or missing real anomalies (higher sigma).

## 4. Investigated Dynamic Per-Feature Sigma Using Coefficient of Variation
To improve sensitivity for stable features and reduce false positives for volatile ones, I tried dynamic sigma per feature per gateway using the **Coefficient of Variation (CV)** but the resulting Dynamic feature rarely shifted from original SIGMA value i.e., but around 0.1 to 0.3 for 1 or two prediction per 8 week Prediction.

    Coefficient of Variation (CV) = Standard Deviation / abs(mean)
    SIGMA = SIGMA * (1 + CV)

## 5. Updated Machine Learning Approach
Upon Closer Inspection of other Datasets and translated the German Text using AI i've concluded with following Outcomes:
    1. The field_visits.csv data provides details of the Gateway reports where the Technician Visited. Upon Translating the texts the following data is obtained
| German                | English                         |
|-----------------------|---------------------------------|
| Kunde meldet Ausfall  | Customer reports an outage      |
| Fehler behoben        | Issue resolved                  |
| Kein Zugang           | No access                       |
| Kein Fehler gefunden  | No issue found                  |

Here based on the values we can consider the Gateways with **Fehler behoben** outcome as Anomaly and the Gateways with **Kein Fehler gefunden** outcome as Normal Gateways aggregating these findings in our model helps in making our prediction rankings more accurate.

The Updated Findings is intergrated with the meter readings data from other datasets includings gateway_master.csv, meter_read_success.csv for better accuracy in rankings 

## 6. Why Choose Machine Learning
- The baseline model developed only checks the standard deviation of a single feature and ranks the gateways based on the difference.
- This method is not efficient for real-world scenarios. Therefore, using Machine Learning to identify gateways with the largest anomalous behaviour is a better approach for solving the problem.