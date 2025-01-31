import riskfolio as rp

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
        "mean_variance": w_mv.squeeze().to_dict(),
        "cvar": w_cvar.squeeze().to_dict(),
        "erc": w_erc.squeeze().to_dict()
    }
