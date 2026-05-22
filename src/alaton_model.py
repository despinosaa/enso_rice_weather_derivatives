"""Modelo de temperatura Alaton et al. (2002).

Estructura: T_m(t) = A + B*t + C*sin(2*pi*t/365 + phi) + componente OU.
Calibración por OLS sobre residuales del componente estacional, siguiendo
el patrón de S12 Mean Reversion del curso.

Funciones esperadas:
    fit_seasonal_trend(...)
    fit_ou_residuals(...)
    simulate_paths(...)
"""
