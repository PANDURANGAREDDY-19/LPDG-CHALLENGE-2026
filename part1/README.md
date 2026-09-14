# Part 1 — Sigma Anomaly Baseline

## Overview

A per-gateway sigma anomaly detector. For each Monday in the scored window, gateways are ranked by the number of anomalous hours in the trailing 7 days and the top 15 are selected.

## Method

For each Monday in the scored window:

1. Take the trailing 28 days of telemetry per gateway, strictly before that Monday.
2. Per gateway, compute the mean and standard deviation of 42 selected features.
3. Flag any hour in the trailing 7 days where a feature exceeds its gateway's mean by more than sigma threshold.
5. Rank gateways by flagged-hour count and take the top 15.

## Feature Selection

Features are selected using two filters applied in sequence:

- **Variance Threshold** — drops features with variance ≤ 0.01 (near-constant, no signal).
- **Correlation Threshold** — drops one of any pair of features with absolute correlation ≥ 0.95, keeping the one with fewer missing or invalid values.
- The Feature in Correlation Pair with More Null Values or Missing Values are removed instead of removing the first feature blindly.

The 42 selected features are:

['rx_nr_pkts', 'tx_success', 'tx_busy', 'number_of_messages', 'avg_idletime', 'avg_load1', 'load1_bigger1', 'load1_bigger2', 'avg_memfree', 'avg_uptime', 'avg_activeproccess', 'avg_totalproccess', 'reboot_cnt', 'reboot_duration_sec', 'r_cnt_power_cycle', 'r_cnt_reboot', 'r_cnt_unknown', 'r_dur_power_cycle', 'r_dur_reboot', 'r_dur_unknown', 'avg_reboot_duration', 'disconnection_cnt', 'offline_duration_sec', 'avg_offline_duration', 'online_duration_mins', 'no_conn_importance', 'network_2g', 'network_3g', 'network_4g', 'network_unknown', 'operator_O2DE', 'operator_TelekomDE', 'operator_VodafoneDE', 'rssi_good', 'rssi_normal', 'rssi_bad', 'rscp_rsrp_good', 'rscp_rsrp_normal', 'rscp_rsrp_bad', 'ecio_rsrq_good', 'ecio_rsrq_normal', 'ecio_rsrq_bad']

## Usage
```bash
python part1/baseline.py --data path/to/data --out predictions.csv