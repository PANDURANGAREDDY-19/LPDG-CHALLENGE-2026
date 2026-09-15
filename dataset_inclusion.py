import datetime as dt
import pathlib
import numpy as np
import pandas as pd

DATA = pathlib.Path("data")

def extract_visit_labels(end: pd.Timestamp, days: int = 28) -> pd.DataFrame:
    df = pd.read_csv(DATA / "field_visits.csv", parse_dates=["requested_on"], dayfirst=False)
    df = df[df["outcome"] == "Fehler behoben"]
    start = end - dt.timedelta(days=days)
    mask = (df["requested_on"] >= start.tz_localize(None)) & (df["requested_on"] < end.tz_localize(None))
    counts = (
        df[mask]
        .groupby("gateway_id")
        .size()
        .rename("confirmed_anomaly_count")
        .reset_index()
    )
    return counts

def enrich_gateway_features() -> pd.DataFrame:
    df = pd.read_csv(DATA / "gateway_master.csv", parse_dates=["installed_on"], encoding="latin-1")
    ref = pd.Timestamp("2026-02-02")
    df["gateway_age_days"] = (ref - df["installed_on"]).dt.days.fillna(0).astype(int)
    df = df[["gateway_id", "hw_model", "site_type", "antenna_type", "gateway_age_days", "n_meters_installed"]]
    return pd.get_dummies(df, columns=["hw_model", "site_type", "antenna_type"])

def compute_read_ratio(end: pd.Timestamp, days: int = 28) -> pd.DataFrame:
    df = pd.read_csv(DATA / "meter_read_success.csv", parse_dates=["week_start"])
    df["gateway_id"] = df["gateway_id"].str.upper().apply(
        lambda x: ":".join(x[i : i + 2] for i in range(0, 12, 2))
    )
    df["read_ratio"] = df["meters_read"] / df["meters_expected"].replace(0, np.nan)
    start = end - dt.timedelta(days=days)
    window = df[
        (df["week_start"] >= start.tz_localize(None))
        & (df["week_start"] < end.tz_localize(None))
    ]
    agg = (
        window.groupby("gateway_id")["read_ratio"]
        .agg(read_ratio_mean="mean", read_ratio_min="min", read_ratio_std="std")
        .fillna(0)
        .reset_index()
    )
    return agg