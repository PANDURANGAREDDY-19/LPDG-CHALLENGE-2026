import numpy as np
import pandas as pd
import pathlib
from sklearn.feature_selection import VarianceThreshold

def load_data():
    data = pd.read_parquet(pathlib.Path("data") / "telemetry")
    data["ts"] = pd.to_datetime(data["ts_utc"], utc=True)
    return data

data = load_data()

def DatasetVarianceThreshold():
    features = data.drop(columns=["ts", "gateway_id", "DateDt", "month"])
    features = features.select_dtypes(include=[np.number])
    selector = VarianceThreshold(threshold=0.01)
    selector.fit(features)
    return features.columns[selector.get_support()].to_list()

def CorrelationThreshold():
    cols = DatasetVarianceThreshold()
    features = data[cols]
    correlation = features.corr().abs()
    upper_tri = correlation.where(np.triu(np.ones(correlation.shape), k=1).astype(bool))
    to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > 0.95)]
    selected_columns = [column for column in features.columns if column not in to_drop]
    return selected_columns

def features_selection_validity():
    frame = pd.read_parquet(pathlib.Path("data") / "telemetry")
    frame["ts"] = pd.to_datetime(frame["ts_utc"], utc=True)
    selector = VarianceThreshold(threshold=0.01)
    dtypes = frame.drop(columns=["ts", "gateway_id","DateDt","month"])
    dtypes = dtypes.select_dtypes(include=[np.number])
    selector.fit(dtypes)
    selected_columns = dtypes.columns[selector.get_support()]
    print(f"Selected columns: {list(selected_columns)}")
    print(f"Variance of all columns: {dtypes[dtypes.columns].var()}")
    print(f"Dropped columns: {list(set(dtypes.columns) - set(selected_columns))}")
    print(f"Variance of dropped columns: {dtypes[list(set(dtypes.columns) - set(selected_columns))].var()}")