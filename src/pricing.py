"""Valoración de derivados climáticos por Monte Carlo.

Sigue patrón S11 Option Pricing by Monte Carlo Simulation:
    payoff = np.maximum(index - K, 0)        # call HDD
    payoff = np.maximum(K - index, 0)        # put CRI
    price = exp(-r*T) * mean(payoff)

Dos modos: lambda = 0 (baseline) y lambda calibrado (Cao & Wei, 2004).
"""
