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


def calculate_efficient_frontier(X, num_points=100):
    """
    Calculate the efficient frontier using CVaR as the risk measure.
    Uses riskfolio-lib to generate optimal portfolio allocations.

    Parameters:
    - X (pd.DataFrame): Daily returns of assets
    - num_points (int): Number of points to calculate on the frontier

    Returns:
    - dict: Contains risks (CVaR), returns, and sharpe ratios for each point
    """
    if X.empty or len(X.columns) < 2:
        print(f"Not enough stocks for efficient frontier. Columns: {len(X.columns) if not X.empty else 0}")
        return None

    try:
        # Create Portfolio object with the original data first
        port = rp.Portfolio(returns=X)

        # Set estimation methods
        method_mu = 'hist'
        method_cov = 'hist'
        port.assets_stats(method_mu=method_mu, method_cov=method_cov)
        
        # Calculate efficient frontier using Standard Deviation (Volatility)
        rm = 'MV'  # Use Mean-Variance (Standard Deviation) as risk measure
        points = num_points

        # Generate efficient frontier weights
        frontier_weights = port.efficient_frontier(model='Classic', rm=rm, points=points, rf=0, hist=True)

        if frontier_weights is None or frontier_weights.empty:
            return None

        # Calculate risk and return for each portfolio on the frontier
        portfolio_returns = []
        portfolio_risks = []

        # Check for extreme outliers that might cause unrealistic values
        max_return = X.abs().max().max()
        
        # Filter out extreme outliers (daily returns > 10% are typically data errors)
        outlier_threshold = 0.10  # 10% daily return threshold
        extreme_returns = X.abs() > outlier_threshold
        
        if extreme_returns.any().any():
            # Replace extreme values with NaN (they'll be dropped)
            X_filtered = X.copy()
            X_filtered[extreme_returns] = np.nan
            
            # Drop rows with any extreme values
            X = X_filtered.dropna()
            
            # Check if we still have enough data
            if X.empty or len(X) < 30:  # Need at least 30 days of data
                return None
            
            # Recreate Portfolio object with filtered data
            port = rp.Portfolio(returns=X)
            port.assets_stats(method_mu=method_mu, method_cov=method_cov)
            
            # Regenerate efficient frontier weights with filtered data
            frontier_weights = port.efficient_frontier(model='Classic', rm=rm, points=points, rf=0, hist=True)
            
            if frontier_weights is None or frontier_weights.empty:
                return None
            
        # Check if returns are already in percentage form (values > 1)
        if max_return > 1:
            X = X / 100  # Convert from percentage to decimal

        for i in range(frontier_weights.shape[1]):
            weights = frontier_weights.iloc[:, i].values.reshape(-1, 1)

            # Calculate expected return (annualized using t_factor=252)
            # port.mu now contains daily expected returns from filtered data
            expected_return = np.dot(weights.T, port.mu.values.reshape(-1, 1))[0, 0] * 252
            portfolio_returns.append(expected_return * 100)  # Convert to percentage

            # Calculate Standard Deviation (Volatility) for the portfolio
            portfolio_daily_returns = (X.values @ weights).flatten()
            
            # Calculate daily standard deviation
            daily_std = np.std(portfolio_daily_returns)
            
            # Annualize standard deviation by multiplying by sqrt(252)
            annualized_std = daily_std * np.sqrt(252) * 100  # Convert to percentage
            
            portfolio_risks.append(annualized_std)

        portfolio_returns = np.array(portfolio_returns)
        portfolio_risks = np.array(portfolio_risks)

        # Calculate Sharpe ratios
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
        import traceback
        traceback.print_exc()
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
