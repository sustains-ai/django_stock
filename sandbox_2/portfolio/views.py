
from .models import Portfolio, FundManager,HistoricalStockData
from .forms import StockForm, PortfolioForm
from django.contrib.auth import logout
from django.core.cache import cache
import pandas as pd
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Portfolio, HistoricalStockData, Stock
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
import json
import pandas as pd
from .models import Portfolio, Stock, HistoricalStockData
from .risk_analysis import perform_risk_analysis, calculate_risk_measures
import json
from django.shortcuts import render
from django.shortcuts import redirect
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

from .risk_analysis import calculate_portfolio_risk
from django.shortcuts import render, get_object_or_404
import pandas as pd
from .models import Portfolio, HistoricalStockData
from .risk_analysis import perform_risk_analysis  # Import new function

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm

from .decorators import fund_manager_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

import os
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from dotenv import load_dotenv

load_dotenv()  # Ensures .env is loaded if not already

import os
import requests
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

from .utils import fetch_news_sentiment,global_open_closed_status
from .ai_agent import portfolio_risk_agent




def custom_login(request):
    form = AuthenticationForm(data=request.POST or None)
    news_data = fetch_news_sentiment()
    news_fetch_success = bool(news_data)  # True if news_data is not empty, False otherwise
    print("✅ News fetch success:", news_fetch_success)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("/portfolio_list/")
    print("🟡 Login page loaded")

    return render(request, 'portfolio/login.html', {
        'form': form,
        'news_data': news_data,
        'news_fetch_success': news_fetch_success
    })




def logout_view(request):
    logout(request)
    return redirect('login')  # or redirect('/') if you prefer




def index(request):
    return render(request, 'portfolio/index.html')


@login_required
@fund_manager_required
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





@login_required
def add_stock(request):
    portfolios = Portfolio.objects.filter(fund_manager__user=request.user)
    if request.method == "POST":
        form = StockForm(request.POST)
        if form.is_valid():
            stock_data = form.save(commit=False)
            portfolio_id = request.POST.get("portfolio_id")
            if not portfolio_id:
                messages.error(request, "Please select a portfolio!")
                return render(request, "portfolio/add_stock.html", {"form": form, "portfolios": portfolios})

            portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)
            stock_data.portfolio = portfolio

            existing_stock = portfolio.stocks.filter(symbol=stock_data.symbol).first()
            if existing_stock:
                total_quantity = existing_stock.quantity + stock_data.quantity
                weighted_price = (
                    (existing_stock.price * existing_stock.quantity) +
                    (stock_data.price * stock_data.quantity)
                ) / total_quantity
                existing_stock.quantity = total_quantity
                existing_stock.price = weighted_price
                existing_stock.save()
                messages.success(request, f"Updated {stock_data.symbol} in {portfolio.name}")
            else:
                stock_data.save()
                if stock_data.fetch_and_store_historical_data():
                    messages.success(request, f"Added {stock_data.symbol} to {portfolio.name} with Alpha Vantage data")
                else:
                    messages.warning(request, f"Added {stock_data.symbol} to {portfolio.name}, but failed to fetch Alpha Vantage data")
            return redirect("analyze_portfolio",portfolio_id=portfolio.id)
        else:
            messages.error(request, "Invalid stock data. Please check the form.")
    else:
        form = StockForm()
    return render(request, "portfolio/add_stock.html", {"form": form, "portfolios": portfolios})



from django.views.decorators.http import require_POST

@login_required
@require_POST
def delete_stock(request, portfolio_id, symbol):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)
    stock = portfolio.stocks.filter(symbol=symbol).first()

    if stock:
        stock.delete()
        messages.success(request, f'Stock {symbol} has been removed from {portfolio.name}.')
    else:
        messages.warning(request, f'Stock {symbol} not found in this portfolio.')

    return redirect('analyze_portfolio', portfolio_id=portfolio.id)










@login_required
def analyze_portfolio(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)
    stocks = portfolio.stocks.all()

    # Calculate stock data and total value
    stock_data = []
    total_value = 0
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
                'manual_price': float(manual_price) if manual_price else None,
                'live_price': live_price,
                'total_value': float(stock_total),
            })

    # Fetch historical prices
    historical_prices_qs = HistoricalStockData.objects.filter(portfolio=portfolio).order_by("date")
    if not historical_prices_qs.exists():
        messages.warning(request, "No historical data available for this portfolio.")
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'stock_data': stock_data,
            'total_value': float(total_value),
            'historical_data': json.dumps({}),
            'portfolio_analysis': None,
            'risk_measures': {},
        })

    # Convert to DataFrame
    historical_prices_df = pd.DataFrame.from_records(
        historical_prices_qs.values("date", "symbol", "adjusted_close")
    )

    # Pivot to time series and filter available symbols
    daily_prices = historical_prices_df.pivot(index='date', columns='symbol', values='adjusted_close').dropna()
    available_symbols = daily_prices.columns.tolist()
    stock_symbols = [stock.symbol for stock in stocks if stock.symbol in available_symbols]

    # Build historical data for template
    historical_data = {}
    for symbol in stock_symbols:
        symbol_data = historical_prices_df[historical_prices_df["symbol"] == symbol]
        historical_data[symbol] = {
            "dates": symbol_data["date"].astype(str).tolist(),
            "prices": symbol_data["adjusted_close"].tolist()
        }

    # Compute daily returns
    X = daily_prices.pct_change().dropna()
    if X.empty:
        messages.warning(request, "Not enough historical data to compute returns.")
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'stock_data': stock_data,
            'total_value': float(total_value),
            'historical_data': json.dumps(historical_data),
            'portfolio_analysis': None,
            'risk_measures': {},
        })

    # Perform risk analysis
    portfolio_analysis = perform_risk_analysis(X)
    risk_measures = calculate_risk_measures(X, stock_symbols)

    if portfolio_analysis is None:
        messages.warning(request, "Portfolio optimization failed. Ensure enough price data is available.")
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'stock_data': stock_data,
            'total_value': float(total_value),
            'historical_data': json.dumps(historical_data),
            'portfolio_analysis': None,
            'risk_measures': risk_measures,
        })

    # Prepare JSON for template
    portfolio_analysis_json = {
        "mean_variance": json.dumps(portfolio_analysis["mean_variance"]),
        "cvar": json.dumps(portfolio_analysis["cvar"]),
        "erc": json.dumps(portfolio_analysis["erc"]),
    }

    # ✅ Compute portfolio value over time for Plotly chart
    portfolio_values = (daily_prices[stock_symbols] * pd.Series(
        {stock.symbol: stock.quantity for stock in stocks if stock.symbol in stock_symbols}
    )).sum(axis=1)

    portfolio_value_json = portfolio_values.reset_index()
    portfolio_value_json["date"] = portfolio_value_json["date"].astype(str)
    portfolio_value_json.columns = ["x", "y"]  # Required for Plotly
    portfolio_value_json = portfolio_value_json.to_dict(orient="records")

    ai_answer = None
    if request.method == "POST" and "ai_question" in request.POST:
        question = request.POST.get("ai_question")
        ai_answer = portfolio_risk_agent(portfolio_id, question)


    return render(request, 'portfolio/analyze_portfolio.html', {
        'portfolio': portfolio,
        'stock_data': stock_data,
        'total_value': float(total_value),
        'historical_data': json.dumps(historical_data or []),
        'portfolio_analysis': portfolio_analysis_json,
        'optimal_table': portfolio_analysis,
        'risk_measures': risk_measures,
        'portfolio_value_json': json.dumps(portfolio_value_json or []),
        'ai_answer': ai_answer,

    })





@login_required
def portfolio_risk(request, portfolio_id):
    """
    Computes risk measures for the entire portfolio and tracks portfolio value over time.
    """
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)
    stocks = portfolio.stocks.all()

    # Fetch historical stock data
    historical_prices_qs = HistoricalStockData.objects.filter(portfolio=portfolio).order_by("date")
    if not historical_prices_qs.exists():
        messages.warning(request, "No historical data available to calculate portfolio risk.")
        return render(request, "portfolio/analyze_portfolio.html", {
            "portfolio": portfolio,
        })

    # Convert to DataFrame
    df = pd.DataFrame.from_records(historical_prices_qs.values("date", "symbol", "adjusted_close"))
    price_data = df.pivot(index="date", columns="symbol", values="adjusted_close").ffill()

    # Filter stocks with historical data
    available_symbols = price_data.columns.tolist()
    valid_stocks = [stock for stock in stocks if stock.symbol in available_symbols]
    if not valid_stocks:
        messages.warning(request, "No valid stocks with historical data for risk calculation.")
        return render(request, "portfolio/analyze_portfolio.html", {
            "portfolio": portfolio,
        })

    # Compute daily returns
    X = price_data[available_symbols].pct_change().dropna()
    if X.empty:
        messages.warning(request, "Not enough historical data to compute returns.")
        return render(request, "portfolio/analyze_portfolio.html", {
            "portfolio": portfolio,
        })

    # Portfolio weights (equal weights for available stocks)
    portfolio_weights = {stock.symbol: 1 / len(available_symbols) for stock in valid_stocks}

    # Calculate portfolio risk
    portfolio_risk_measures = calculate_portfolio_risk(X, portfolio_weights)

    # Fetch stock quantities for valid stocks
    stock_quantities = {stock.symbol: stock.quantity for stock in valid_stocks}

    # Compute portfolio value over time
    portfolio_values = (price_data[available_symbols] * pd.Series(stock_quantities)).sum(axis=1)

    # Convert portfolio value to JSON
    portfolio_value_json = portfolio_values.reset_index()
    portfolio_value_json["date"] = portfolio_value_json["date"].astype(str)
    # portfolio_value_json = portfolio_value_json.rename(columns={"date": "x", 0: "y"}).to_dict(orient="records")
    portfolio_value_json.columns = ["x", "y"]  # ✅ Important fix
    portfolio_value_json = portfolio_value_json.to_dict(orient="records")



    print("DEBUG: Portfolio Value JSON")
    print(json.dumps(portfolio_value_json, indent=4))

    # Context for template
    context = {
        "portfolio": portfolio,
        "portfolio_risk_measures": portfolio_risk_measures,
        "portfolio_id": portfolio.id,
        "portfolio_value_json": json.dumps(portfolio_value_json),
    }

    return render(request, "portfolio/analyze_portfolio.html", context)






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



# def market_status_view(request):
#     cache_key = "latest_market_status"
#     fallback_data = cache.get(cache_key)
#
#     try:
#         market_data = global_open_closed_status()
#         if market_data and "markets" in market_data:
#             cache.set(cache_key, market_data, timeout=3600)  # 1 hour
#             return JsonResponse(market_data)
#         else:
#             raise ValueError("Invalid structure or empty response")
#     except Exception as e:
#         print(f"❌ Serving fallback from cache: {e}")
#         if fallback_data:
#             return JsonResponse(fallback_data)
#         return JsonResponse({"error": "Failed to fetch market status"}, status=500)

from django.http import JsonResponse

def market_status_view(request):
        market_data = global_open_closed_status()
        response= JsonResponse(market_data,safe=False)
        print("Response Content:", response.content.decode('utf-8'))  # Debug output
        return response


# views.py

from django.shortcuts import render
from .ai_agent import portfolio_risk_agent

def ask_ai_view(request, portfolio_id):
    answer = ""
    if request.method == "POST":
        question = request.POST.get("question")
        answer = portfolio_risk_agent(portfolio_id, question)
    return render(request, "portfolio/ask_ai.html", {"answer": answer})


# views.py
from django.http import JsonResponse
from .utils import fetch_news_sentiment


def fetch_news_view(request, portfolio_id):
    news = fetch_news_sentiment()
    return JsonResponse({"news": news[:5]})  # Send only top 5


# views.py
from django.http import JsonResponse
from .utils import fetch_currency_exchange_rates

def fetch_currency_rates(request,portfolio_id):
    try:
        rates = fetch_currency_exchange_rates()
        return JsonResponse({"exchange_rates": rates})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

from .utils import fetch_treasury_yield


def fetch_treasury_yield_view(request, portfolio_id):
    try:
        raw = fetch_treasury_yield()  # This returns the full history
        if not raw or "data" not in raw:
            return JsonResponse({"error": "Data unavailable"}, status=500)

        entries = raw["data"][:36]  # Last 36 monthly yields
        labels = [e["date"] for e in reversed(entries)]
        values = [float(e["value"]) for e in reversed(entries)]

        return JsonResponse({"labels": labels, "values": values})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)