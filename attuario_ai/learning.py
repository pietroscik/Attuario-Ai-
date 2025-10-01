from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class EvaluationResult:
    """Risultati sintetici della valutazione del modello."""

    mae: float
    rmse: float
    r2: float
    details: Dict[str, float]


def _train_linear_regression(
    X: np.ndarray, y: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Stima una regressione lineare con minimi quadrati (senza sklearn).
    Restituisce (coef, y_pred).
    """
    # Aggiunge il bias (intercetta)
    ones = np.ones((X.shape[0], 1), dtype=float)
    Xb = np.hstack((ones, X))
    coef, *_ = np.linalg.lstsq(Xb, y, rcond=None)
    y_pred = Xb @ coef
    return coef, y_pred


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> EvaluationResult:
    """Calcola metriche classiche di regressione."""
    resid = y_true - y_pred
    mae = float(np.mean(np.abs(resid)))
    rmse = float(np.sqrt(np.mean(resid**2)))
    # R^2
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return EvaluationResult(
        mae=mae,
        rmse=rmse,
        r2=r2,
        details={"ss_res": ss_res, "ss_tot": ss_tot},
    )


class Learner:
    """
    Esegue una pipeline minimale:
    - preprocess (dropna, selezione colonne)
    - split train/test
    - stima regressione lineare
    - metriche su test
    """

    def __init__(
        self,
        data: pd.DataFrame,
        target: str,
        features: Optional[List[str]] = None,
        test_size: float = 0.2,
        seed: Optional[int] = None,
    ) -> None:
        self.data = data.copy()
        self.target = target
        self.features = features or [c for c in self.data.columns if c != target]
        self.test_size = max(0.0, min(0.9, float(test_size)))
        self.seed = seed

    def preprocess(self) -> pd.DataFrame:
        cols = [*self.features, self.target]
        df = self.data.loc[:, cols].dropna()
        # Cast numerico “robusto”
        for c in cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna()
        return df

    def _split(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        n = len(df)
        n_test = max(1, int(round(self.test_size * n)))
        idx = np.arange(n)
        rng = np.random.default_rng(self.seed)
        rng.shuffle(idx)
        test_idx = idx[:n_test]
        train_idx = idx[n_test:]
        X = df[self.features].to_numpy(dtype=float)
        y = df[self.target].to_numpy(dtype=float)
        return X[train_idx], y[train_idx], X[test_idx], y[test_idx]

    def fit_evaluate(self) -> EvaluationResult:
        df = self.preprocess()
        if len(df) < 3:
            # Dataset troppo piccolo: fallback “semplice”
            y = df[self.target].to_numpy(dtype=float)
            y_hat = np.repeat(np.mean(y), len(y))
            return _metrics(y, y_hat)

        X_tr, y_tr, X_te, y_te = self._split(df)
        coef, _ = _train_linear_regression(X_tr, y_tr)
        # Predizione su test
        ones = np.ones((X_te.shape[0], 1), dtype=float)
        Xb_te = np.hstack((ones, X_te))
        y_pred = Xb_te @ coef
        return _metrics(y_te, y_pred)


def main() -> None:
    # Esempio demo: y ~ 2*x1 + 0.5*x2 + rumore
    rng = np.random.default_rng(42)
    n = 120
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    y = 2.0 * x1 + 0.5 * x2 + rng.normal(0, 0.3, n)
    df = pd.DataFrame({"x1": x1, "x2": x2, "y": y})
    learner = Learner(df, target="y", features=["x1", "x2"], test_size=0.2, seed=7)
    result = learner.fit_evaluate()
    print(f"MAE={result.mae:.3f} | RMSE={result.rmse:.3f} | R2={result.r2:.3f}")


if __name__ == "__main__":
    main()
