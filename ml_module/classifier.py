"""
classifier.py
Clasificador supervisado para predecir probabilidad de conversión a cliente.
Sistema de Inteligencia de Mercado Don Piotr

Usa RandomForestClassifier binario: cliente (1) vs no-cliente (0).
El desbalance de clases se maneja con SMOTE en cada fold de CV y
class_weight='balanced' en el modelo final.
"""

import logging
from typing import Dict

import numpy as np
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    make_scorer,
)
from sklearn.model_selection import StratifiedKFold, cross_validate

from ml_module import config as ml_config

logger = logging.getLogger("ml_module.classifier")


class ConversionClassifier:
    """Clasificador supervisado de conversión a cliente.

    Entrena un RandomForest binario usando la etiqueta derivada del
    estado 'cliente' en la BD. El desbalance de clases se maneja con
    SMOTE dentro de cada fold de validación cruzada y class_weight='balanced'
    en el entrenamiento final.

    Uso:
        clf = ConversionClassifier()
        metrics = clf.fit_and_validate(X, y)
        probs = clf.predict_proba(X)
    """

    def __init__(self) -> None:
        self.model = RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=ml_config.RANDOM_STATE,
            n_jobs=-1,
        )
        self._is_fitted = False

    def fit_and_validate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Entrena el modelo y retorna métricas de validación cruzada.

        Usa StratifiedKFold-3 con SMOTE aplicado solo en el conjunto de
        entrenamiento de cada fold para evitar data leakage. El modelo
        final se entrena con todos los datos sin SMOTE.

        Args:
            X: Matriz de features (n_samples, n_features).
            y: Vector de etiquetas binarias (1=cliente, 0=no-cliente).

        Returns:
            Dict con accuracy, precision, recall, f1, auc_roc,
            cv_mean (media F1 en CV), cv_std, y support_positive.
        """
        n_positives = int(y.sum())
        n_total = len(y)
        logger.info(f"Clasificador: {n_positives} clientes de {n_total} restaurantes")

        if n_positives < 2:
            logger.warning("Menos de 2 clientes — clasificador omitido")
            return {}

        # k=3 para que cada fold de test tenga ~1/3 de los positivos
        # (más estable que k=5 con datasets pequeños)
        n_splits = min(3, n_positives)
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=ml_config.RANDOM_STATE)

        # SMOTE dentro del pipeline para que solo afecte al set de entrenamiento
        # de cada fold (evita data leakage hacia el set de validación)
        k_neighbors = min(5, n_positives - 1)
        cv_pipeline = ImbPipeline([
            ("smote", SMOTE(random_state=ml_config.RANDOM_STATE, k_neighbors=k_neighbors)),
            ("clf", RandomForestClassifier(
                n_estimators=200,
                class_weight="balanced",
                random_state=ml_config.RANDOM_STATE,
                n_jobs=-1,
            )),
        ])

        scoring = {
            "accuracy": make_scorer(accuracy_score),
            "precision": make_scorer(precision_score, zero_division=0),
            "recall": make_scorer(recall_score, zero_division=0),
            "f1": make_scorer(f1_score, zero_division=0),
        }
        cv_results = cross_validate(
            cv_pipeline, X, y,
            cv=cv,
            scoring=scoring,
            return_train_score=False,
        )

        cv_f1_mean = float(np.mean(cv_results["test_f1"]))
        cv_f1_std = float(np.std(cv_results["test_f1"]))

        logger.info(f"CV F1 (SMOTE, k={n_splits}): {cv_f1_mean:.4f} ± {cv_f1_std:.4f}")

        # Entrenar modelo final con todos los datos (sin SMOTE — datos reales)
        self.model.fit(X, y)
        self._is_fitted = True

        y_pred = self.model.predict(X)
        y_proba = self.model.predict_proba(X)[:, 1]

        metrics = {
            "accuracy": round(float(accuracy_score(y, y_pred)), 4),
            "precision": round(float(precision_score(y, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y, y_pred, zero_division=0)), 4),
            "auc_roc": round(float(roc_auc_score(y, y_proba)), 4),
            "cv_f1_mean": round(cv_f1_mean, 4),
            "cv_f1_std": round(cv_f1_std, 4),
            "support_positive": n_positives,
            "support_total": n_total,
        }

        logger.info(
            f"Métricas finales — Precision: {metrics['precision']:.4f} "
            f"Recall: {metrics['recall']:.4f} F1: {metrics['f1']:.4f} "
            f"AUC-ROC: {metrics['auc_roc']:.4f}"
        )

        return metrics

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Retorna la probabilidad de conversión para cada restaurante.

        Args:
            X: Matriz de features.

        Returns:
            Array de probabilidades [0, 1] para clase positiva (cliente).
        """
        if not self._is_fitted:
            raise RuntimeError("Debe llamar fit_and_validate() primero")
        return self.model.predict_proba(X)[:, 1]

    def get_feature_importances(self, feature_names: list) -> list[dict]:
        """Retorna las features más importantes para la clasificación.

        Args:
            feature_names: Nombres de las features en el mismo orden que X.

        Returns:
            Lista de {feature, importance} ordenada por importancia desc.
        """
        if not self._is_fitted:
            return []
        importances = self.model.feature_importances_
        paired = sorted(
            zip(feature_names, importances),
            key=lambda x: x[1],
            reverse=True,
        )
        return [{"feature": name, "importance": round(float(imp), 4)} for name, imp in paired[:10]]
