"""Construcción de índices climáticos sobre la ventana fenológica del arroz.

Índices:
    HDD = sum(max(T - T*, 0)) sobre ventana, T* = 32C (estrés térmico)
    GDD = sum(max(T - T_base, 0)), T_base = 10C
    CRI = sum(P) sobre ventana de floración y llenado del grano
"""
