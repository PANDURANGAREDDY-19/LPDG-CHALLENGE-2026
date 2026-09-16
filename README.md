# LPDG Challenge 2026 — Gateway Anomaly Detection

A system that identifies the top 15 IoT gateways most likely to need a field engineer visit each week, using telemetry data and machine learning.

## Project Explanation

[![Watch the demo](https://img.youtube.com/vi/1_n2j_eIQUE/0.jpg)](https://youtu.be/1_n2j_eIQUE)

---

## What This Does

Each week, hundreds of gateways report telemetry (signal quality, uptime, disconnections, reboots, etc.). This project ranks gateways by anomaly severity and outputs the top 15 per week across 8 scored weeks (2026-02-02 to 2026-03-23).

---

## Project Structure

```
LPDG-CHALLENGE-2026/
│
├── data/                        # Input data (not committed)
│   ├── telemetry/               # Parquet files with hourly gateway telemetry
│   ├── field_visits.csv         # Historical engineer visit outcomes
│   ├── gateway_master.csv       # Gateway hardware and site metadata
│   └── meter_read_success.csv   # Weekly meter read success rates
│
├── part1/
│   ├── baseline.py              # Extended 3-sigma anomaly baseline (42 features)
│   ├── DECISIONS.md             # Design decisions and rationale
│   └── README.md                # Part 1 specific documentation
│
├── data_selection.py            # Feature selection (variance + correlation filters)
├── dataset_inclusion.py         # Supplementary feature engineering
├── model.py                     # ML model — Isolation Forest + LOF ensemble
├── baseline_3sigma.py           # Company reference baseline (3 metrics only)
├── compare.py                   # Compare two prediction CSV outputs
├── predictions.py               # Score new data using saved model
│
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Docker service configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## Requirements

- Python 3.11+
- Docker Desktop (optional, for containerised run)

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Quick Start

### Option 1 — Run Locally

**Extended baseline (42 features, bidirectional spike detection):**
```bash
py part1/baseline.py --data data --out predictions_baseline.csv
```

**ML model (Isolation Forest + LOF ensemble):**
```bash
py model.py
```
Outputs `predictions_model.csv` and saves trained models to `models.pkl`.

**Company reference baseline (3 metrics only):**
```bash
py baseline_3sigma.py --data data --out predictions_3sigma.csv
```

### Option 2 — Run via Docker

```bash
docker compose up --build
```
Outputs `data/predictions.csv` via volume mount.

---

## Output Format

All prediction files follow this schema:

| Column | Description |
|---|---|
| `week_start` | Monday date of the scored week (e.g. `2026-02-02`) |
| `rank` | 1–15, where 1 is the highest priority gateway |
| `gateway_id` | Gateway MAC address (colon-separated hex) |
| `score` | Anomaly score (higher = more anomalous) |
| `reason` | Human-readable explanation of why the gateway was flagged |

Validate any output file:
```bash
py test/validate_submission.py predictions_model.csv
```

---

## Comparing Outputs

Use `compare.py` to compare any two prediction files:

```bash
py compare.py part1/predictions_baseline.csv predictions_model.csv
```

Shows per-week overlap, rank correlation, gateway frequency, and score distribution between the two files.

---

## Scoring New Data (ML Model)

Once `model.py` has been run and `models.pkl` exists, score a new week without retraining:

```bash
py predictions.py --week 2026-02-02
```

For a week outside the trained window:
```bash
py predictions.py --week 2026-04-07 --end 2026-04-14
```

---

## Approaches

### 1. Company Baseline — `baseline_3sigma.py`
- Flags hours where `offline_duration_sec`, `disconnection_cnt`, or `reboot_cnt` exceed `mean + 3σ` of the gateway's own 28-day history
- Ranks by total flagged hours in the last 7 days
- Simple, interpretable, and used as the reference bar

### 2. Extended Baseline — `part1/baseline.py`
- Same 3-sigma logic but applied to 42 features selected via variance and correlation filtering
- Directional spike detection per feature:
  - **Upward only** — `offline_duration_sec`, `disconnection_cnt`, `reboot_cnt`, `avg_offline_duration`
  - **Downward only** — `number_of_messages`, `avg_uptime`, `avg_activeproccess`, `avg_totalproccess`, `online_duration_mins`
  - **Both directions** — all remaining features

### 3. ML Ensemble — `model.py`
- Builds per-gateway feature vectors (mean/std/max of 42 metrics over 28-day window)
- Enriches with gateway metadata, meter read ratios, and historical fault counts
- Scores using two unsupervised models:
  - **Isolation Forest** — detects globally rare gateways
  - **Local Outlier Factor** — detects locally dense outliers
- Combines scores via **Borda count rank aggregation**
- Saves trained models per week to `models.pkl` for reuse

---

## Data Notes

- `gateway_master.csv` uses **latin-1 encoding** (German umlauts — `Gebäude`, `Außenmast`)
- `meter_read_success.csv` uses no-colon hex gateway IDs (`0202CB0A6B1F`) — normalised to colon format (`02:02:CB:0A:6B:1F`) automatically
- `field_visits.csv` outcomes are in German:

| German | English |
|---|---|
| Fehler behoben | Fault confirmed and resolved |
| Kein Fehler gefunden | No fault found |
| Kein Zugang | No access |
| Kunde meldet Ausfall | Customer reports outage |

---

## Docker Notes

- Base image: `python:3.11-slim`
- Mounts `./data` to `/app/data` inside the container
- Output written to `./data/predictions.csv`
- To switch which script Docker runs, update the `CMD` line in `Dockerfile`

---

## Key Design Decisions

See [`part1/DECISIONS.md`](part1/DECISIONS.md) for full rationale. Summary:

- **Why 42 features instead of 3** — more signals reduce the chance of missing anomalies that don't manifest in offline/disconnection/reboot metrics alone
- **Why directional spike detection** — a drop in `avg_activeprocess` to 0 is a fault signal; an upward-only check would miss it entirely
- **Why Isolation Forest + LOF** — IF finds globally rare gateways; LOF finds locally unusual ones; combining both via Borda count is more robust than either alone
- **Why sigma = 3.0** — no labelled ground truth available to tune an alternative threshold
