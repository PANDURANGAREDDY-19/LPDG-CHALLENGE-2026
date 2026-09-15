from __future__ import annotations

import argparse
import datetime as dt
import pathlib

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from data_selection import CorrelationThreshold, load_data
from dataset_inclusion import compute_read_ratio, enrich_gateway_features, extract_visit_labels

cols = CorrelationThreshold()
METRICS = [col for col in cols if col not in ["gateway_id", "ts", "DateDt", "ts_utc"]]
_GATEWAY_FEATURES = enrich_gateway_features()
SCORED_WEEKS = [dt.date(2026, 2, 2) + dt.timedelta(days=7 * i) for i in range(8)]
VISITS_PER_WEEK = 15
BASELINE_DAYS = 28
RECENT_DAYS = 7


def build_gateway_features(frame: pd.DataFrame, end: pd.Timestamp, days: int) -> pd.DataFrame:
    window = frame[(frame["ts"] >= end - dt.timedelta(days=days)) & (frame["ts"] < end)]
    if window.empty:
        return pd.DataFrame()
    features = window.groupby("gateway_id")[METRICS].agg(["mean", "std", "max"])
    features.columns = ["_".join(c) for c in features.columns]
    features = features.fillna(0).reset_index()
    features = features.merge(_GATEWAY_FEATURES, on="gateway_id", how="left")
    features = features.merge(compute_read_ratio(end, days), on="gateway_id", how="left")
    visit_labels = extract_visit_labels(end, days)
    features = features.merge(visit_labels, on="gateway_id", how="left")
    features["confirmed_anomaly_count"] = features["confirmed_anomaly_count"].fillna(0)
    return features.set_index("gateway_id").fillna(0)

def scale_features(X: pd.DataFrame) -> tuple[np.ndarray, StandardScaler]:
    scaler = StandardScaler()
    return scaler.fit_transform(X), scaler

def score_isolation_forest(X: np.ndarray) -> np.ndarray:
    clf = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
    clf.fit(X)
    return -clf.score_samples(X)

def score_lof(X: np.ndarray) -> np.ndarray:
    clf = LocalOutlierFactor(n_neighbors=min(20, len(X) - 1), contamination="auto")
    clf.fit_predict(X)
    return -clf.negative_outlier_factor_

def borda_count(scores: list[np.ndarray]) -> np.ndarray:
    n = len(scores[0])
    borda = np.zeros(n)
    for s in scores:
        ranks = np.argsort(np.argsort(s)) 
        borda += ranks
    return borda

def models_agreed(scores: list[np.ndarray], top_k: int) -> np.ndarray:
    n = len(scores[0])
    agreement = np.zeros(n, dtype=int)
    for s in scores:
        top_indices = set(np.argsort(s)[-top_k:])
        for i in top_indices:
            agreement[i] += 1
    return agreement

def rank_week(frame: pd.DataFrame, monday: dt.date) -> pd.DataFrame:
    end = pd.Timestamp(monday, tz="UTC")
    baseline_features = build_gateway_features(frame, end, BASELINE_DAYS)
    if baseline_features.empty:
        return pd.DataFrame(columns=["gateway_id", "score", "models_agreed"])
    recent_features = build_gateway_features(frame, end, RECENT_DAYS)
    if recent_features.empty:
        return pd.DataFrame(columns=["gateway_id", "score", "models_agreed"])

    recent_features = recent_features.reindex(columns=baseline_features.columns, fill_value=0)
    common_gateways = baseline_features.index.intersection(recent_features.index)
    if len(common_gateways) < VISITS_PER_WEEK:
        return pd.DataFrame(columns=["gateway_id", "score", "models_agreed"])

    X_baseline, _ = scale_features(baseline_features.loc[common_gateways])

    if_scores = score_isolation_forest(X_baseline)
    lof_scores = score_lof(X_baseline)
    ensemble = borda_count([if_scores, lof_scores])
    agreement = models_agreed([if_scores, lof_scores], top_k=VISITS_PER_WEEK)

    result = pd.DataFrame({
        "gateway_id": common_gateways,
        "score": ensemble,
        "models_agreed": agreement,
    })
    return result.sort_values("score", ascending=False).reset_index(drop=True)

def build_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for monday in SCORED_WEEKS:
        ranked = rank_week(frame, monday)
        if len(ranked) < VISITS_PER_WEEK:
            raise SystemExit(f"only {len(ranked)} gateways have data before {monday}")
        for rank, row in enumerate(ranked.head(VISITS_PER_WEEK).itertuples(index=False), 1):
            rows.append({
                "week_start": monday.isoformat(),
                "rank": rank,
                "gateway_id": row.gateway_id,
                "score": float(row.score),
                "reason": (
                    f"Ensemble anomaly score {row.score:.1f}; "
                    f"flagged by {row.models_agreed}/2 models"
                ),
            })
    return pd.DataFrame(rows)

def main(argv: list[str] | None = None) -> int:
    here = pathlib.Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    default_data = here / "data" if (here / "data").exists() else here.parent / "student-brief" / "data"
    parser.add_argument("--data", type=pathlib.Path, default=default_data)
    parser.add_argument("--out", type=pathlib.Path, default=here / "predictions_model.csv")
    args = parser.parse_args(argv)
    data = load_data()
    frame = data[["gateway_id", "ts", *METRICS]].copy()
    predictions = build_predictions(frame)
    predictions.to_csv(args.out, index=False)
    print(f"wrote {args.out} — {len(predictions)} rows over {predictions.week_start.nunique()} weeks")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())