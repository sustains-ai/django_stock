
from .models import Portfolio, FundManager,HistoricalStockData
from .forms import StockForm, PortfolioForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .risk_analysis import calculate_risk_measures
from django.http import JsonResponse
import numpy as np
import riskfolio as rp
from django.shortcuts import render, get_object_or_404, redirect
from .models import Portfolio, Stock, HistoricalStockData
from .forms import StockForm
from .utils import fetch_and_store_historical_data
from .risk_analysis import calculate_portfolio_risk
from django.shortcuts import render, get_object_or_404
import pandas as pd
from .models import Portfolio, HistoricalStockData
from .risk_analysis import perform_risk_analysis  # Import new function



def index(request):
    return render(request, 'portfolio/index.html')



def portfolio_list(request):
    portfolios = Portfolio.objects.filter(fund_manager__user=request.user)
    return render(request, 'portfolio/portfolio_list.html', {'portfolios': portfolios})

@login_required
def add_portfolio(request):
    if request.method == 'POST':
        form = PortfolioForm(request.POST)
        if form.is_valid():
            portfolio = form.save(commit=False)  # Don't save to the database yet
            # Associate the portfolio with the logged-in user's fund manager
            try:
                portfolio.fund_manager = FundManager.objects.get(user=request.user)
                portfolio.save()  # Now save to the database
                return redirect('portfolio_list')
            except FundManager.DoesNotExist:
                return render(request, 'portfolio/error.html', {'message': 'No FundManager associated with this user.'})
    else:
        form = PortfolioForm()
    return render(request, 'portfolio/add_portfolio.html', {'form': form})





def add_stock(request):
    portfolios = Portfolio.objects.filter(fund_manager__user=request.user)

    if request.method == "POST":
        form = StockForm(request.POST)

        if form.is_valid():
            stock_data = form.save(commit=False)
            portfolio_id = request.POST.get("portfolio_id")

            if not portfolio_id:
                return render(request, "portfolio/add_stock.html", {
                    "form": form,
                    "portfolios": portfolios,
                    "error": "Please select a portfolio!"
                })

            portfolio = get_object_or_404(Portfolio, id=portfolio_id)
            stock_data.portfolio = portfolio

            # ✅ Check if the stock already exists in the portfolio
            existing_stock = portfolio.stocks.filter(symbol=stock_data.symbol).first()

            if existing_stock:
                # ✅ Weighted Average Price Calculation
                total_quantity = existing_stock.quantity + stock_data.quantity
                weighted_price = (
                    (existing_stock.price * existing_stock.quantity) +
                    (stock_data.price * stock_data.quantity)
                ) / total_quantity

                # ✅ Update existing stock
                existing_stock.quantity = total_quantity
                existing_stock.price = weighted_price
                existing_stock.save()

            else:
                # ✅ Add as new stock if it doesn't exist
                stock_data.save()

                # ✅ Fetch historical data only if not already stored
                existing_data = HistoricalStockData.objects.filter(
                    portfolio=portfolio, symbol=stock_data.symbol
                ).exists()

                if not existing_data:
                    fetch_and_store_historical_data(portfolio.id, stock_data.symbol)

            return redirect("portfolio_list")

    else:
        form = StockForm()

    return render(request, "portfolio/add_stock.html", {
        "form": form,
        "portfolios": portfolios
    })






def analyze_portfolio(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)
    stocks = portfolio.stocks.all()

    stock_data = []
    total_value = 0
    historical_data = {}

    stock_symbols = [stock.symbol for stock in stocks]

    for stock in stocks:
        manual_price = stock.price
        live_price = stock.get_live_price()
        price = manual_price if manual_price else live_price

        if price is not None:
            stock_total = price * stock.quantity
            total_value += stock_total
            stock_data.append({
                'name': stock.name,
                'symbol': stock.symbol,
                'quantity': stock.quantity,
                'manual_price': manual_price,
                'live_price': live_price,
                'total_value': stock_total,
            })

    # Fetch historical prices
    historical_prices_qs = HistoricalStockData.objects.filter(
        portfolio=portfolio, symbol__in=stock_symbols).order_by("date")

    if not historical_prices_qs.exists():
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'stock_data': stock_data,
            'total_value': total_value,
            'historical_data': json.dumps({}),
            'portfolio_analysis': None,
            'risk_measures': {},
            'error': "No historical data available for this portfolio."
        })

    # Convert to DataFrame
    historical_prices_df = pd.DataFrame.from_records(
        historical_prices_qs.values("date", "symbol", "adjusted_close")
    )

    for symbol in stock_symbols:
        symbol_data = historical_prices_df[historical_prices_df["symbol"] == symbol]
        historical_data[symbol] = {
            "dates": list(symbol_data["date"].astype(str)),
            "prices": list(symbol_data["adjusted_close"])
        }

        if historical_prices_df.empty:
            return render(request, 'portfolio/analyze_portfolio.html', {
                'portfolio': portfolio,
                'stock_data': stock_data,
                'total_value': total_value,
                'historical_data': json.dumps({}),  # ✅ Ensure JSON format
                'portfolio_analysis': None,
                'risk_measures': {},
                'error': "No historical data available for this portfolio."
            })

            # Convert historical prices to JSON
        for symbol in stock_symbols:
            symbol_data = historical_prices_df[historical_prices_df["symbol"] == symbol]
            historical_data[symbol] = {
                "dates": list(symbol_data["date"].astype(str)),
                "prices": list(symbol_data["adjusted_close"])
            }

            # ✅ Convert historical_data to JSON properly
        historical_data_json = json.dumps(historical_data)








            # Pivot the data to get a time series
    daily_prices = historical_prices_df.pivot(index='date', columns='symbol', values='adjusted_close')
    daily_prices = daily_prices.dropna().reset_index(drop=True)

    # Compute daily returns
    X = daily_prices.pct_change().dropna().reset_index(drop=True)

    if X.empty:
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'stock_data': stock_data,
            'total_value': total_value,
            'historical_data': {},
            'portfolio_analysis': None,
            'risk_measures': {},
            'error': "Not enough historical price data to compute returns."
        })

    # ✅ Call risk analysis function
    portfolio_analysis = perform_risk_analysis(X)
    risk_measures = calculate_risk_measures(X, stock_symbols)



    # ✅ Ensure JSON is formatted correctly

    portfolio_analysis_json = {
        "mean_variance": json.dumps(portfolio_analysis["mean_variance"]),  # ✅ Correct dictionary access
        "cvar": json.dumps(portfolio_analysis["cvar"]),
        "erc": json.dumps(portfolio_analysis["erc"]),
    }

    if portfolio_analysis is None:
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'stock_data': stock_data,
            'total_value': total_value,
            'historical_data': {},
            'portfolio_analysis': None,
            'risk_measures': risk_measures,
            'error': "Portfolio optimization failed. Ensure enough price data is available."
        })



    return render(request, 'portfolio/analyze_portfolio.html', {
        'portfolio': portfolio,
        'stock_data': stock_data,
        'total_value': total_value,
        'historical_data': json.dumps(historical_data),
        'portfolio_analysis': portfolio_analysis_json,
        "optimal_table": portfolio_analysis,
        'risk_measures': risk_measures
    })






def portfolio_risk(request, portfolio_id):
    """
    Computes risk measures for the entire portfolio.
    """

    portfolio = get_object_or_404(Portfolio, id=portfolio_id)

    # ✅ Fetch historical stock data
    historical_prices_qs = HistoricalStockData.objects.filter(portfolio=portfolio).order_by("date")

    if not historical_prices_qs.exists():
        return render(request, "portfolio/portfolio_risk.html", {
            "portfolio": portfolio,
            "error": "No historical data available to calculate portfolio risk.",
        })

    # ✅ Convert to DataFrame
    df = pd.DataFrame.from_records(historical_prices_qs.values("date", "symbol", "adjusted_close"))
    price_data = df.pivot(index="date", columns="symbol", values="adjusted_close")

    # ✅ Compute daily returns
    X = price_data.pct_change(fill_method=None).dropna()

    # ✅ Get optimal portfolio weights (from previous portfolio analysis)
    portfolio_weights = {
        stock.symbol: 1 / len(price_data.columns)  # Placeholder: Equal Weights
        for stock in portfolio.stocks.all()
    }

    # ✅ Calculate portfolio risk
    portfolio_risk_measures = calculate_portfolio_risk(X, portfolio_weights)

    # ✅ Pass portfolio risk to template
    context = {
        "portfolio": portfolio,
        "portfolio_risk_measures": portfolio_risk_measures,
        "portfolio_id": portfolio.id,
    }

    return render(request, "portfolio/portfolio_risk.html", context)









def calculate_efficient_frontier(X, portfolio_weights):
    """
    Computes the Efficient Frontier using standard deviation (volatility) as the risk measure.
    """
    # Create Portfolio object
    port = rp.Portfolio(returns=X)

    # Estimate expected returns & covariance
    port.assets_stats(method_mu="hist", method_cov="hist")

    # Compute efficient frontier
    points = 50  # Number of portfolios
    rm = "MV"  # Mean-Variance (Standard Deviation) Risk Measure
    hist = True
    w_frontier = port.efficient_frontier(model="Classic", rm=rm, points=points, hist=hist)

    # Compute portfolio returns and standard deviation
    mu = port.mu.values.flatten()  # Expected returns
    sigma = port.cov.values  # Covariance matrix

    frontier_returns = np.dot(w_frontier.T, mu)  # Portfolio expected return
    frontier_risks = np.sqrt(np.einsum('ij,jk,ik->i', w_frontier.T, sigma, w_frontier.T))  # Portfolio volatility

    # Format output as risk-return points
    efficient_frontier_data = [{"x": float(frontier_risks[i]), "y": float(frontier_returns[i])} for i in range(points)]

    return efficient_frontier_data


def load_risk_measure(request, portfolio_id, measure):
    print(f"🔹 Received request for {measure} of portfolio {portfolio_id}")

    valid_measures = ["std_dev", "var", "cvar"]
    if measure not in valid_measures:
        print("❌ Invalid measure requested")
        return JsonResponse({"error": "Invalid measure"}, status=400)

    portfolio = get_object_or_404(Portfolio, id=portfolio_id)

    historical_prices_qs = HistoricalStockData.objects.filter(portfolio=portfolio).order_by("date")
    if not historical_prices_qs.exists():
        print("❌ No historical data available")
        return JsonResponse({"error": "No historical data available"}, status=400)

    df = pd.DataFrame.from_records(historical_prices_qs.values("date", "symbol", "adjusted_close"))
    price_data = df.pivot(index="date", columns="symbol", values="adjusted_close")

    print("📊 Price Data:")
    print(price_data.head())  # Print first few rows for debugging

    X = price_data.pct_change(fill_method=None).dropna()
    print("📈 Returns Data:")
    print(X.head())  # Print first few rows

    portfolio_weights = {
        stock.symbol: 1 / len(price_data.columns)  # Placeholder: Equal weights
        for stock in portfolio.stocks.all()
    }
    print("⚖️ Portfolio Weights:", portfolio_weights)

    portfolio_risk_measures = calculate_portfolio_risk(X, portfolio_weights)
    print("🔢 Portfolio Risk Measures:", portfolio_risk_measures)

    # ✅ Select only the requested measure

    # Map measure names to correct keys
    measure_mapping = {
        "std_dev": "Std_Dev",
        "var": "VaR_95",
        "cvar": "CVaR_95",
    }

    # Get the correct key from the mapping
    normalized_key = measure_mapping.get(measure, None)

    if normalized_key is None:
        return JsonResponse({"error": "Invalid measure requested"}, status=400)

    print(f"🔍 Looking for key: {normalized_key}")  # Debugging

    risk_value = portfolio_risk_measures.get(normalized_key, None)

    # If it's a NumPy array, extract the value
    if isinstance(risk_value, np.ndarray):
        risk_value = float(risk_value[0, 0])  # Extract the scalar

    print(f"✅ Returning Risk Measure ({measure}): {risk_value}")
    return JsonResponse({measure: risk_value})


def delete_portfolio(request, portfolio_id):
    if request.method == "POST":
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)
        portfolio_name = portfolio.name
        portfolio.delete()
        messages.success(request, f'Portfolio "{portfolio_name}" has been deleted successfully.')
    return redirect('portfolio_list')


import json
from django.shortcuts import render

def std_dev_view(request, portfolio_id):
    # ✅ Fetch Portfolio Data (Ensure it's always available)
    portfolio_weights = {'AAPL': 0.2, 'TSLA': 0.2, 'GOOG': 0.2, 'META': 0.2, 'MSFT': 0.2}
    efficient_frontier_data = [
        {"x": 0.15, "y": 0.08},
        {"x": 0.20, "y": 0.10},
        {"x": 0.25, "y": 0.12}
    ]  # Example Data

    # ✅ Convert to JSON for JavaScript
    portfolio_weights_json = json.dumps(portfolio_weights)
    efficient_frontier_json = json.dumps(efficient_frontier_data)

    return render(request, "portfolio/std_dev.html", {
        "portfolio_weights_json": portfolio_weights_json,
        "efficient_frontier_json": efficient_frontier_json,
    })
