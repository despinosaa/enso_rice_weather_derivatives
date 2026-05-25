import numpy as np
import pandas as pd
import statsmodels.api as sm
from typing import Tuple, Dict


def modelar_temperatura_alaton(
    df_dpto: pd.DataFrame,
    frecuencia: str = "diaria",
    modelo_estacional: str = "1_armonico",
) -> Tuple[pd.DataFrame, Dict[str, float], sm.regression.linear_model.RegressionResultsWrapper]:
    """
    Modelo Alaton con selección descriptiva de armónicos.

    modelo_estacional = "1_armonico"   -> 1 armónico + tendencia lineal
    modelo_estacional = "2_armonicos"  -> 2 armónicos + tendencia lineal

    Mantiene la misma lógica de calibración, simulación y agregación.
    No incluye prints ni visualizaciones.
    """
    freq_map = {
        "diaria": "D",
        "mensual": "ME",
        "trimestral": "QE",
        "semestral": "6ME",
        "anual": "YE",
    }
    frec_code = freq_map.get(frecuencia.lower())
    if frec_code is None:
        raise ValueError(f"frecuencia '{frecuencia}' no válida. Opciones: {list(freq_map)}")

    if modelo_estacional not in ("1_armonico", "2_armonicos"):
        raise ValueError("modelo_estacional debe ser '1_armonico' o '2_armonicos'")

    temp = df_dpto.copy()
    d = temp.index.dayofyear

    if modelo_estacional == "1_armonico":
        X_ols = sm.add_constant(pd.DataFrame({
            "sin": np.sin(2 * np.pi * d / 365),
            "cos": np.cos(2 * np.pi * d / 365),
        }, index=temp.index))
    else:
        X_ols = sm.add_constant(pd.DataFrame({
            "t": np.arange(len(temp)),
            "sin": np.sin(2 * np.pi * d / 365),
            "cos": np.cos(2 * np.pi * d / 365),
            "sin2": np.sin(4 * np.pi * d / 365),
            "cos2": np.cos(4 * np.pi * d / 365),
        }, index=temp.index))

    ols_model = sm.OLS(temp["t_mean"], X_ols).fit()
    temp["seasonal_fit"] = ols_model.predict(X_ols)
    temp["residuals"] = temp["t_mean"] - temp["seasonal_fit"]

    temp["res_lag"] = temp["residuals"].shift(1)
    ou_data = temp.dropna()
    ou_model = sm.OLS(ou_data["residuals"], sm.add_constant(ou_data["res_lag"])).fit()

    alpha = ou_model.params.get("const", ou_model.params.iloc[0])
    phi = ou_model.params.get("res_lag", ou_model.params.iloc[-1])

    if phi >= 0.99:
        phi = 0.95

    kappa = -np.log(phi)
    sigma = np.sqrt(ou_model.mse_resid)

    n = len(temp)
    sim_res = np.zeros(n)
    for t in range(1, n):
        sim_res[t] = alpha + phi * sim_res[t - 1] + np.random.normal(0, sigma)

    temp["T_sim"] = temp["seasonal_fit"] + sim_res

    df_agg = temp[["t_mean", "seasonal_fit", "T_sim", "residuals"]].resample(frec_code).mean()

    params = {
        "phi": float(phi),
        "kappa": float(kappa),
        "sigma": float(sigma),
        "frecuencia_salida": frecuencia,
        "modelo_estacional": modelo_estacional,
    }
    return df_agg, params, ols_model