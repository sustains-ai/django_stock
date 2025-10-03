import pandas as pd
import numpy as np
import riskfolio as rp
from django.core.cache import cache
from functools import lru_cache

def perform_risk_analysis(X):
    """
    Perform risk analysis and optimization on the portfolio.
    :param X: DataFrame of historical returns
    :return: Dictionary containing optimized weights for different models
    """
    if X.empty:
        return None  # Not enough data for risk analysis

    # Create Portfolio object
    port = rp.Portfolio(returns=X)

    # Set estimation methods
    method_mu = 'hist'  # Historical expected returns
    method_cov = 'hist'  # Historical covariance matrix
    port.assets_stats(method_mu=method_mu, method_cov=method_cov)

    # Portfolio Optimization Parameters
    model = 'Classic'
    rf = 0  # Risk-free rate
    hist = True

    # --- 1. Mean-Variance Optimization (MV) ---
    w_mv = port.optimization(model=model, rm='MV', obj='Sharpe', rf=rf, hist=hist)

    # --- 2. Conditional Value at Risk (CVaR) Optimization ---
    w_cvar = port.optimization(model=model, rm='CVaR', obj='Sharpe', rf=rf, hist=hist)

    # --- 3. Equal Risk Contribution (ERC) Portfolio ---
    w_erc = port.rp_optimization(model=model, rm='MV', rf=rf, hist=hist)

    if w_mv.empty or w_cvar.empty or w_erc.empty:
        return None  # Optimization failed

    return {
        # "mean_variance": w_mv.squeeze().to_dict(),
        # "cvar": w_cvar.squeeze().to_dict(),
        # "erc": w_erc.squeeze().to_dict()
        "mean_variance": (
            w_mv.squeeze().to_dict() if isinstance(w_mv.squeeze(), pd.Series) else w_mv.squeeze().item()
        ),
        "cvar": (
            w_cvar.squeeze().to_dict() if isinstance(w_cvar.squeeze(), pd.Series) else w_cvar.squeeze().item()
        ),
        "erc": (
            w_erc.squeeze().to_dict() if isinstance(w_erc.squeeze(), pd.Series) else w_erc.squeeze().item()
        )

    }



# def calculate_risk_measures(returns, stock_symbols):
#     risk_measures = {}
#     for symbol in stock_symbols:
#         stock_returns = returns[symbol]
#         risk_measures[symbol] = {
#             "MAD": rp.MAD(stock_returns),
#             "Volatility": np.std(stock_returns),
#             "VaR_95": np.percentile(stock_returns, 5),  # Changed key here
#             "CVaR_95": stock_returns[stock_returns <= np.percentile(stock_returns, 5)].mean(),  # Changed key here
#             "Max_Drawdown": (stock_returns.cumsum().cummax() - stock_returns.cumsum()).max()  # Changed key here
#         }
#     return risk_measures

def calculate_risk_measures(returns, stock_symbols):
    risk_measures = {}
    for symbol in stock_symbols:
        stock_returns = returns[symbol]
        var_95 = np.percentile(stock_returns, 5)
        cvar_95 = stock_returns[stock_returns <= var_95].mean()

        risk_measures[symbol] = {
            "MAD": rp.MAD(stock_returns),
            "Volatility": np.std(stock_returns),
            "VaR_95": -var_95,  # Make it positive
            "CVaR_95": -cvar_95,  # Make it positive
            "Max_Drawdown": (stock_returns.cumsum().cummax() - stock_returns.cumsum()).max()
        }
    return risk_measures


def calculate_efficient_frontier(X, num_points=20):
    """
    Calculate the efficient frontier with multiple portfolio combinations.
    Optimized version with better memory management and vectorized operations.

    Parameters:
    - X (pd.DataFrame): Daily returns of assets
    - num_points (int): Number of points to calculate on the frontier

    Returns:
    - dict: Contains risks, returns, and sharpe ratios for each point
    """
    if X.empty or len(X.columns) < 2:
        return None

    try:
        # Create Portfolio object
        port = rp.Portfolio(returns=X)

        # Set estimation methods
        method_mu = 'hist'
        method_cov = 'hist'
        port.assets_stats(method_mu=method_mu, method_cov=method_cov)

        # Calculate efficient frontier
        points = num_points
        frontier = port.efficient_frontier(model='Classic', rm='MV', points=points, rf=0, hist=True)

        if frontier is None or frontier.empty:
            return None

        # Vectorized calculations for better performance
        weights_array = frontier.values
        mu_array = port.mu.values.flatten()
        cov_matrix = port.cov.values

        # Calculate portfolio returns (annualized) - vectorized
        portfolio_returns = np.dot(weights_array.T, mu_array) * 252

        # Calculate portfolio risks (annualized volatility) - vectorized
        portfolio_variances = np.sum(
            weights_array * np.dot(cov_matrix, weights_array), axis=0
        )
        portfolio_risks = np.sqrt(portfolio_variances) * np.sqrt(252)

        # Calculate Sharpe ratios - vectorized
        sharpe_ratios = np.divide(
            portfolio_returns,
            portfolio_risks,
            out=np.zeros_like(portfolio_returns),
            where=portfolio_risks > 0
        )

        return {
            'risks': portfolio_risks.tolist(),
            'returns': portfolio_returns.tolist(),
            'sharpe_ratios': sharpe_ratios.tolist()
        }

    except Exception as e:
        print(f"Error calculating efficient frontier: {e}")
        return None


def calculate_portfolio_risk(X, weights):
    """
    Computes portfolio-level risk measures using Riskfolio-Lib.

    Parameters:
    - X (pd.DataFrame): Daily returns of assets in the portfolio.
    - weights (dict): Optimal portfolio weights for each asset.

    Returns:
    - dict: Portfolio risk measures including Std Dev, VaR, and CVaR.
    """
    if X.empty or not weights:
        return {
            "Portfolio Std Dev": None,
            "Portfolio VaR": None,
            "Portfolio CVaR": None,
        }

    # Filter weights to only include symbols that exist in X.columns
    available_symbols = [symbol for symbol in X.columns if symbol in weights]
    if not available_symbols:
        return {
            "Std_Dev": None,
            "VaR_95": None,
            "CVaR_95": None,
        }

    # Create filtered DataFrame and weights
    X_filtered = X[available_symbols]
    weights_filtered = {symbol: weights[symbol] for symbol in available_symbols}
    
    # Normalize weights to sum to 1
    total_weight = sum(weights_filtered.values())
    if total_weight > 0:
        weights_filtered = {symbol: weight/total_weight for symbol, weight in weights_filtered.items()}

    # Convert weights to a numpy array
    w = np.array([weights_filtered[symbol] for symbol in X_filtered.columns]).reshape(-1, 1)

    try:
        # Compute portfolio standard deviation (Volatility)
        portfolio_std_dev = np.sqrt(np.dot(w.T, np.dot(X_filtered.cov(), w)))[0, 0]

        # Compute historical VaR and CVaR
        portfolio_returns = X_filtered @ w
        portfolio_var_95 = rp.VaR_Hist(portfolio_returns, alpha=0.05)
        portfolio_cvar_95 = rp.CVaR_Hist(portfolio_returns, alpha=0.05)

        return {
            "Std_Dev": portfolio_std_dev,
            "VaR_95": portfolio_var_95,
            "CVaR_95": portfolio_cvar_95,
        }
    except Exception as e:
        print(f"Error in calculate_portfolio_risk: {e}")
        return {
            "Std_Dev": None,
            "VaR_95": None,
            "CVaR_95": None,
        }
