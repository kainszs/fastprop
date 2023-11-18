# given a filepath and some target columns,
# retrieve the data as numpy arrays

from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer

import numpy as np

import warnings


def preprocess(mordred_descriptors, targets):
    target_scaler = MinMaxScaler()
    y = target_scaler.fit_transform(targets.reshape(-1, 1))

    X = None
    imp_mean = SimpleImputer(missing_values=np.nan, strategy="mean")
    with warnings.catch_warnings():
        warnings.filterwarnings(action="ignore", message="Skipping features without any observed values.*")
        cleaned_mordred_descs = imp_mean.fit_transform(mordred_descriptors, targets)
    del mordred_descriptors

    # scale each column 0-1
    feature_scaler = MinMaxScaler()
    cleaned_normalized_mordred_descs = feature_scaler.fit_transform(cleaned_mordred_descs, targets)
    print("size after clean (drop empty, impute missing, scale 0-1):", cleaned_normalized_mordred_descs.shape)
    del cleaned_mordred_descs

    # drop low variance features
    X = VarianceThreshold(threshold=0).fit_transform(cleaned_normalized_mordred_descs, y)
    print("size after invariant feature removal:", X.shape)
    del cleaned_normalized_mordred_descs

    if not np.isfinite(X).all():
        raise RuntimeError("Postprocessing failed finite check, please file a bug report.")

    return X, y, target_scaler