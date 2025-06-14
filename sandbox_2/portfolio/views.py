from .utils import fetch_treasury_yield
from .utils import fetch_news_sentiment, global_open_closed_status
# To catch potential Redis connection issues
from redis.exceptions import RedisError
from django.http import HttpResponse, HttpResponseServerError
from .utils import get_treasury_yields
from .utils import get_market_returns
from collections import defaultdict
from .utils import monte_carlo_portfolio_var_cvar  # Assuming this is correct
from .models import Portfolio, HistoricalStockData  # Assuming these are correct
from .utils import monte_carlo_portfolio_var_cvar
from .utils import fetch_currency_exchange_rates
from .utils import fetch_news_sentiment
from django.views.decorators.http import require_POST
from .ai_agent import portfolio_risk_agent
from django.utils.timezone import now
from datetime import datetime

from .models import Portfolio, FundManager, HistoricalStockData
from .forms import StockForm, PortfolioForm
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
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

from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm

from .decorators import fund_manager_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from dotenv import load_dotenv

load_dotenv()  # Ensures .env is loaded if not already


def custom_login(request):
    form = AuthenticationForm(data=request.POST or None)
    news_data = fetch_news_sentiment()
    # True if news_data is not empty, False otherwise
    news_fetch_success = bool(news_data)
    print("✅ News fetch success:", news_fetch_success)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("/portfolio_list/")
    print("🟡 Login page loaded")

    return render(request, 'portfolio/login.html', {
        'timestamp': datetime.now().timestamp(),
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
    return render(request,
                  'portfolio/portfolio_list.html',
                  {'portfolios': portfolios})


@login_required
def add_portfolio(request):
    if request.method == 'POST':
        form = PortfolioForm(request.POST)
        if form.is_valid():
            # Don't save to the database yet
            portfolio = form.save(commit=False)
            # Associate the portfolio with the logged-in user's fund manager
            try:
                portfolio.fund_manager = FundManager.objects.get(
                    user=request.user)
                portfolio.save()  # Now save to the database
                return redirect('portfolio_list')
            except FundManager.DoesNotExist:
                return render(request, 'portfolio/error.html',
                              {'message': 'No FundManager associated with this user.'})
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
                return render(request, "portfolio/add_stock.html",
                              {"form": form, "portfolios": portfolios})

            portfolio = get_object_or_404(
                Portfolio, id=portfolio_id, fund_manager__user=request.user)
            stock_data.portfolio = portfolio

            existing_stock = portfolio.stocks.filter(
                symbol=stock_data.symbol).first()
            if existing_stock:
                total_quantity = existing_stock.quantity + stock_data.quantity
                weighted_price = (
                    (existing_stock.price * existing_stock.quantity) +
                    (stock_data.price * stock_data.quantity)
                ) / total_quantity
                existing_stock.quantity = total_quantity
                existing_stock.price = weighted_price
                existing_stock.save()
                messages.success(
                    request, f"Updated {
                        stock_data.symbol} in {
                        portfolio.name}")
            else:
                stock_data.save()
                if stock_data.fetch_and_store_historical_data():
                    messages.success(
                        request, f"Added {
                            stock_data.symbol} to {
                            portfolio.name} with Alpha Vantage data")
                else:
                    messages.warning(
                        request, f"Added {
                            stock_data.symbol} to {
                            portfolio.name}, but failed to fetch Alpha Vantage data")
            return redirect("analyze_portfolio", portfolio_id=portfolio.id)
        else:
            messages.error(
                request, "Invalid stock data. Please check the form.")
    else:
        form = StockForm()
    return render(request, "portfolio/add_stock.html",
                  {"form": form, "portfolios": portfolios})


@login_required
@require_POST
def delete_stock(request, portfolio_id, symbol):
    portfolio = get_object_or_404(
        Portfolio,
        id=portfolio_id,
        fund_manager__user=request.user)
    stock = portfolio.stocks.filter(symbol=symbol).first()

    if stock:
        stock.delete()
        messages.success(
            request,
            f'Stock {symbol} has been removed from {
                portfolio.name}.')
    else:
        messages.warning(
            request,
            f'Stock {symbol} not found in this portfolio.')

    return redirect('analyze_portfolio', portfolio_id=portfolio.id)


@never_cache
@login_required
def analyze_portfolio(request, portfolio_id):
    portfolio = get_object_or_404(
        Portfolio,
        id=portfolio_id,
        fund_manager__user=request.user)
    stocks = portfolio.stocks.all()

    # Calculate total value and structure stock data
    stock_data = []
    total_value = 0
    stock_symbols = []

    for stock in stocks:
        manual_price = stock.price
        try:
            live_price = stock.get_live_price()
        except Exception as e:
            print(f"⚠️ Error fetching live price for {stock.symbol}: {e}")
            live_price = None

        price = manual_price or live_price
        if price is not None:
            stock_total = price * stock.quantity
            total_value += stock_total
            stock_symbols.append(stock.symbol)

            stock_data.append({
                'name': stock.name,
                'symbol': stock.symbol,
                'quantity': stock.quantity,
                'manual_price': float(manual_price) if manual_price else None,
                'live_price': float(live_price) if live_price else None,
                'total_value': float(stock_total),
            })

    # Fetch historical stock data
    historical_qs = HistoricalStockData.objects.filter(
        portfolio=portfolio).order_by("date")

    if not historical_qs.exists():
        messages.warning(
            request,
            "No historical data available for this portfolio.")
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'stock_data': stock_data,
            'total_value': float(total_value),
            'historical_data': json.dumps({}),
            'portfolio_analysis': None,
            'risk_measures': {},
            'portfolio_value_json': json.dumps([]),
            'ai_answer': None,
            'timestamp': int(now().timestamp())
        })

    df = pd.DataFrame.from_records(
        historical_qs.values(
            "date", "symbol", "adjusted_close"))
    if df.empty:
        messages.warning(request, "Historical data exists but is empty.")
        return render(...)

    # Pivot time series
    pivot_df = df.pivot(
        index='date',
        columns='symbol',
        values='adjusted_close').dropna()
    available_symbols = pivot_df.columns.tolist()
    filtered_symbols = [s for s in stock_symbols if s in available_symbols]

    if not filtered_symbols:
        messages.warning(
            request,
            "None of the stocks have valid historical data.")
        return render(...)

    # Build historical data for chart
    historical_data = {
        symbol: {
            "dates": df[df["symbol"] == symbol]["date"].astype(str).tolist(),
            "prices": df[df["symbol"] == symbol]["adjusted_close"].tolist()
        } for symbol in filtered_symbols
    }

    # Compute daily returns
    X = pivot_df[filtered_symbols].pct_change().dropna()
    if X.empty:
        messages.warning(
            request,
            "Not enough historical data to compute returns.")
        return render(...)

    # Risk analysis
    portfolio_analysis = perform_risk_analysis(X)
    risk_measures = calculate_risk_measures(X, filtered_symbols)

    if not portfolio_analysis:
        messages.warning(
            request,
            "Portfolio optimization failed due to insufficient data.")
        return render(...)

    # Portfolio time series value
    portfolio_values = (pivot_df[filtered_symbols] * pd.Series({
        stock.symbol: stock.quantity for stock in stocks if stock.symbol in filtered_symbols
    })).sum(axis=1)

    portfolio_value_json = portfolio_values.reset_index()
    portfolio_value_json["date"] = portfolio_value_json["date"].astype(str)
    portfolio_value_json.columns = ["x", "y"]
    portfolio_value_json = portfolio_value_json.to_dict(orient="records")

    # Optional: AI Q&A
    ai_answer = None
    if request.method == "POST" and "ai_question" in request.POST:
        ai_answer = portfolio_risk_agent(
            portfolio_id, request.POST.get("ai_question"))

    return render(request, 'portfolio/analyze_portfolio.html', {
        'portfolio': portfolio,
        'stock_data': stock_data,
        'total_value': float(total_value),
        'historical_data': json.dumps(historical_data),
        'portfolio_analysis': {
            "mean_variance": json.dumps(portfolio_analysis.get("mean_variance", {})),
            "cvar": json.dumps(portfolio_analysis.get("cvar", {})),
            "erc": json.dumps(portfolio_analysis.get("erc", {})),
        },
        'optimal_table': portfolio_analysis,
        'risk_measures': risk_measures,
        'portfolio_value_json': json.dumps(portfolio_value_json),
        'ai_answer': ai_answer,
        'timestamp': int(now().timestamp())
    })


@login_required
def portfolio_risk(request, portfolio_id):
    """
    Computes risk measures for the entire portfolio and tracks portfolio value over time.
    """
    portfolio = get_object_or_404(
        Portfolio,
        id=portfolio_id,
        fund_manager__user=request.user)
    stocks = portfolio.stocks.all()

    # Fetch historical stock data
    historical_prices_qs = HistoricalStockData.objects.filter(
        portfolio=portfolio).order_by("date")
    if not historical_prices_qs.exists():
        messages.warning(
            request,
            "No historical data available to calculate portfolio risk.")
        return render(request, "portfolio/analyze_portfolio.html", {
            "portfolio": portfolio,
        })

    # Convert to DataFrame
    df = pd.DataFrame.from_records(
        historical_prices_qs.values(
            "date", "symbol", "adjusted_close"))
    price_data = df.pivot(
        index="date",
        columns="symbol",
        values="adjusted_close").ffill()

    # Filter stocks with historical data
    available_symbols = price_data.columns.tolist()
    valid_stocks = [
        stock for stock in stocks if stock.symbol in available_symbols]
    if not valid_stocks:
        messages.warning(
            request,
            "No valid stocks with historical data for risk calculation.")
        return render(request, "portfolio/analyze_portfolio.html", {
            "portfolio": portfolio,
        })

    # Compute daily returns
    X = price_data[available_symbols].pct_change().dropna()
    if X.empty:
        messages.warning(
            request,
            "Not enough historical data to compute returns.")
        return render(request, "portfolio/analyze_portfolio.html", {
            "portfolio": portfolio,
        })

    # Portfolio weights (equal weights for available stocks)
    portfolio_weights = {
        stock.symbol: 1 /
        len(available_symbols) for stock in valid_stocks}

    # Calculate portfolio risk
    portfolio_risk_measures = calculate_portfolio_risk(X, portfolio_weights)

    # Fetch stock quantities for valid stocks
    stock_quantities = {stock.symbol: stock.quantity for stock in valid_stocks}

    # Compute portfolio value over time
    portfolio_values = (
        price_data[available_symbols] *
        pd.Series(stock_quantities)).sum(
        axis=1)

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
    w_frontier = port.efficient_frontier(
        model="Classic", rm=rm, points=points, hist=hist)

    # Compute portfolio returns and standard deviation
    mu = port.mu.values.flatten()  # Expected returns
    sigma = port.cov.values  # Covariance matrix

    frontier_returns = np.dot(w_frontier.T, mu)  # Portfolio expected return
    frontier_risks = np.sqrt(
        np.einsum(
            'ij,jk,ik->i',
            w_frontier.T,
            sigma,
            w_frontier.T))  # Portfolio volatility

    # Format output as risk-return points
    efficient_frontier_data = [{"x": float(frontier_risks[i]), "y": float(
        frontier_returns[i])} for i in range(points)]

    return efficient_frontier_data


def load_risk_measure(request, portfolio_id, measure):
    print(f"🔹 Received request for {measure} of portfolio {portfolio_id}")

    valid_measures = ["std_dev", "var", "cvar"]
    if measure not in valid_measures:
        print("❌ Invalid measure requested")
        return JsonResponse({"error": "Invalid measure"}, status=400)

    portfolio = get_object_or_404(Portfolio, id=portfolio_id)

    historical_prices_qs = HistoricalStockData.objects.filter(
        portfolio=portfolio).order_by("date")
    if not historical_prices_qs.exists():
        print("❌ No historical data available")
        return JsonResponse(
            {"error": "No historical data available"}, status=400)

    df = pd.DataFrame.from_records(
        historical_prices_qs.values(
            "date", "symbol", "adjusted_close"))
    price_data = df.pivot(
        index="date",
        columns="symbol",
        values="adjusted_close")

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
        messages.success(
            request,
            f'Portfolio "{portfolio_name}" has been deleted successfully.')
    return redirect('portfolio_list')


def std_dev_view(request, portfolio_id):
    # ✅ Fetch Portfolio Data (Ensure it's always available)
    portfolio_weights = {
        'AAPL': 0.2,
        'TSLA': 0.2,
        'GOOG': 0.2,
        'META': 0.2,
        'MSFT': 0.2}
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
# return JsonResponse({"error": "Failed to fetch market status"},
# status=500)


def market_status_view(request):
    market_data = global_open_closed_status()
    response = JsonResponse(market_data, safe=False)
    print("Response Content:", response.content.decode('utf-8'))  # Debug output
    return response


# views.py


def ask_ai_view(request, portfolio_id):
    answer = ""
    if request.method == "POST":
        question = request.POST.get("question")
        answer = portfolio_risk_agent(portfolio_id, question)
    return render(request, "portfolio/ask_ai.html", {"answer": answer})


# views.py


def fetch_news_view(request, portfolio_id):
    news = fetch_news_sentiment()
    return JsonResponse({"news": news[:5]})  # Send only top 5


# views.py

def fetch_currency_rates(request, portfolio_id):
    try:
        rates = fetch_currency_exchange_rates()
        return JsonResponse({"exchange_rates": rates})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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


def monte_carlo_risk_view(request, portfolio_id):
    try:
        print(f"🔍 Starting Monte Carlo risk view for portfolio {portfolio_id}")
        portfolio = Portfolio.objects.get(id=portfolio_id)
        stocks = portfolio.stocks.all()

        price_data = []

        for stock in stocks:
            # Your existing logic for fetching and preparing price data
            records = HistoricalStockData.objects.filter(
                portfolio=portfolio, symbol=stock.symbol).order_by("date")
            if records.exists():
                df = pd.DataFrame(
                    [(r.date, r.adjusted_close) for r in records],
                    columns=["date", stock.symbol]
                ).set_index("date")
                price_data.append(df)
            else:
                # Added portfolio_id for clarity
                print(
                    f"⚠️ Skipping {
                        stock.symbol} due to no data in portfolio {portfolio_id}")

        if not price_data:
            # Added portfolio_id
            print(
                f"❌ No price data found for any stock in portfolio {portfolio_id}")
            # Consider status 400 for client-side correctable errors if appropriate,
            # or if no data means an issue with the portfolio setup.
            # For now, keeping 500 as per your original code.
            return JsonResponse(
                {"error": "No price data found for any stock"}, status=500)

        combined_df = pd.concat(price_data, axis=1, join="inner").dropna()

        # Add a check for empty combined_df after join and dropna
        if combined_df.empty or len(
                combined_df) < 2:  # Need at least 2 rows for shift(1)
            print(
                f"❌ Combined price data is insufficient after join/dropna for portfolio {portfolio_id}")
            return JsonResponse(
                {"error": "Not enough overlapping/valid price data for analysis"}, status=500)  # Or 400

        print(
            f"📊 Price Data (portfolio {portfolio_id}):\n",
            combined_df.head())  # Added portfolio_id

        log_returns = np.log(combined_df / combined_df.shift(1)).dropna()

        # Add a check for empty log_returns
        if log_returns.empty:
            print(f"❌ Log returns are empty for portfolio {portfolio_id}")
            return JsonResponse(
                {"error": "Could not calculate log returns from available price data"}, status=500)  # Or 400

        print(
            f"📈 Returns Data (portfolio {portfolio_id}):\n",
            log_returns.tail())  # Added portfolio_id

        # Ensure there's at least one column of returns for weighting
        if log_returns.shape[1] == 0:
            print(
                f"❌ No valid asset returns columns for portfolio {portfolio_id}")
            return JsonResponse(
                {"error": "No valid asset returns to process"}, status=500)  # Or 400

        weights = np.array([1.0 / log_returns.shape[1]] * log_returns.shape[1])
        portfolio_log_returns = log_returns.dot(weights)

        # Ensure portfolio_log_returns is not empty (e.g., if weights was
        # empty, though unlikely with above check)
        if portfolio_log_returns.empty:
            print(
                f"❌ Portfolio log returns series is empty for portfolio {portfolio_id}")
            return JsonResponse(
                {"error": "Could not calculate portfolio log returns"}, status=500)  # Or 400

        # === ADDITIONS START HERE ===
        # Calculate mean and standard deviation of the portfolio log returns
        mean_return_raw = float(portfolio_log_returns.mean())
        std_dev_return_raw = float(portfolio_log_returns.std())

        # Get VaR and CVaR from your utils function (these are raw, e.g., -0.031)
        # Your function monte_carlo_portfolio_var_cvar already returns these
        var_raw, cvar_raw = monte_carlo_portfolio_var_cvar(
            portfolio_log_returns)

        # Convert all four values to percentages
        var_pct = var_raw * 100
        cvar_pct = cvar_raw * 100
        mean_return_pct = mean_return_raw * 100
        std_dev_return_pct = std_dev_return_raw * 100

        # Construct the JSON response with the keys JavaScript expects
        response_data = {
            "VaR_pct": round(
                var_pct,
                4) if not np.isnan(var_pct) else None,
            "CVaR_pct": round(
                cvar_pct,
                4) if not np.isnan(cvar_pct) else None,
            "mean_return_pct": round(
                mean_return_pct,
                2) if not np.isnan(mean_return_pct) else None,
            "std_dev_return_pct": round(
                    std_dev_return_pct,
                    2) if not np.isnan(std_dev_return_pct) else None,
        }
        # === ADDITIONS END HERE ===

        # Print the data being sent for debugging
        print(
            f"✅ monte_carlo_risk_view for portfolio {portfolio_id} sending data: {response_data}")
        return JsonResponse(response_data)  # Return the new response_data

    # Your existing exception handling
    except Portfolio.DoesNotExist:  # Specific exception first
        print(f"❌ Portfolio with ID {portfolio_id} not found.")
        return JsonResponse({"error": "Portfolio not found"}, status=404)
    except Exception as e:
        print(
            f"❌ Exception occurred in monte_carlo_risk_view for portfolio {portfolio_id}: {e}")
        import traceback  # Import traceback here for more detailed error logging
        traceback.print_exc()  # This will print the full Python traceback to your console
        return JsonResponse({"error": str(e)}, status=500)


def performance_stats(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)
    stocks = Stock.objects.filter(portfolio=portfolio)

    if not stocks.exists():
        return JsonResponse(
            {"error": "No stocks in this portfolio."}, status=404)

    # --- Total Buying Price ---
    total_buying_price = sum(
        (stock.price or 0) *
        stock.quantity for stock in stocks)

    # --- Current Market Value ---
    current_market_value = 0
    for stock in stocks:
        live_price = stock.get_live_price()
        if live_price:
            current_market_value += live_price * stock.quantity
        elif stock.price:  # fallback
            current_market_value += float(stock.price) * stock.quantity

    number_of_holdings = stocks.count()

    # --- Get historical data ---
    historical_data = HistoricalStockData.objects.filter(
        portfolio=portfolio).order_by("date")
    if not historical_data.exists():
        return JsonResponse({
            "total_buying_price": round(total_buying_price, 2),
            "current_market_value": round(current_market_value, 2),
            "number_of_holdings": number_of_holdings,
            "sharpe_ratio": None,
            "beta": None,
            "max_drawdown_pct": None,
            "cumulative_return_pct": None
        })

    # --- Aggregate daily values ---
    daily_values = defaultdict(float)
    for row in historical_data:
        # Already portfolio-linked
        daily_values[row.date] += row.adjusted_close

    sorted_dates = sorted(daily_values)
    values = [daily_values[date] for date in sorted_dates]

    if len(values) < 2:
        return JsonResponse({
            "total_buying_price": round(total_buying_price, 2),
            "current_market_value": round(current_market_value, 2),
            "number_of_holdings": number_of_holdings,
            "sharpe_ratio": None,
            "beta": None,
            "max_drawdown_pct": None,
            "cumulative_return_pct": None
        })

    returns = np.diff(values) / values[:-1]
    market_data = get_market_returns()
    market_return_dict = dict(market_data)

    aligned_returns = []
    for i, date in enumerate(sorted_dates[1:]):
        date_str = date.strftime("%Y-%m-%d")
        if date_str in market_return_dict:
            aligned_returns.append((returns[i], market_return_dict[date_str]))

    if aligned_returns:
        port_ret, mkt_ret = zip(*aligned_returns)
        beta = np.cov(port_ret, mkt_ret)[0][1] / np.var(mkt_ret)
    else:
        beta = None

    sharpe_ratio = np.mean(returns) / np.std(returns) * \
        np.sqrt(252) if len(returns) > 1 else None
    cumulative_return = (values[-1] - values[0]) / \
        values[0] if values[0] else None

    running_max = np.maximum.accumulate(values)
    drawdowns = (values - running_max) / running_max
    max_drawdown = np.min(drawdowns) if len(drawdowns) else None

    treasury_data = get_treasury_yields()
    risk_free_rate = treasury_data.get("10y") if treasury_data else None

    response_data = {
        "total_buying_price": round(total_buying_price, 2),
        "current_market_value": round(current_market_value, 2),
        "number_of_holdings": number_of_holdings,
        "sharpe_ratio": round(sharpe_ratio, 4) if sharpe_ratio else None,
        "beta": beta,
        "max_drawdown_pct": round(max_drawdown, 4) if max_drawdown else None,
        "cumulative_return_pct": round(cumulative_return, 4) if cumulative_return else None,
        "risk_free_rate": round(risk_free_rate, 4) if risk_free_rate else None
    }

    return JsonResponse(response_data)


def get_all_yield_data(request, portfolio_id):

    yields = get_treasury_yields()

    return JsonResponse({"status": "success", "yields": {
        "3m": yields["3m"],
        "2y": yields["2y"],
        "5y": yields["5y"],
        "7y": yields["7y"],
        "10y": yields["10y"],
        "30y": yields["30y"]
    }}, status=200)


# your_app_name/views.py


def test_redis_cache(request):
    key = "my_django_test_key"  # Let's use a slightly more descriptive key
    value_to_set = "Hello from Django, cached in Redis!"
    html_response = "<h1>Redis Cache Test</h1>"

    try:
        # 1. Set a value in the cache
        cache.set(key, value_to_set, timeout=60)  # Cache for 60 seconds
        html_response += f"<p>Attempted to set key '<code>{key}</code>' with value '<code>{value_to_set}</code>'.</p>"

        # 2. Get the value from the cache
        retrieved_value = cache.get(key)
        html_response += f"<p>Attempted to retrieve key '<code>{key}</code>'.</p>"

        if retrieved_value is not None:
            html_response += f"<p style='color: green;'>Value from Redis: <strong>{retrieved_value}</strong></p>"
            if retrieved_value == value_to_set:
                html_response += "<p style='color: green; font-weight: bold;'>SUCCESS: Set and Get values match!</p>"
            else:
                html_response += f"<p style='color: orange; font-weight: bold;'>WARNING: Mismatch! Expected '{value_to_set}', but got '{retrieved_value}'.</p>"
        else:
            html_response += f"<p style='color: red; font-weight: bold;'>ERROR: Value for '<code>{key}</code>' was not found in cache. It might have expired or failed to set.</p>"

        # 3. Optionally, you can try to delete it
        # cache.delete(key)
        # html_response += f"<p>Deleted key '<code>{key}</code>' (if it existed).</p>"

        return HttpResponse(html_response)

    except RedisError as e:
        error_message = (
            f"<h1>Redis Connection Error</h1>"
            f"<p style='color: red;'>An error occurred while trying to communicate with Redis: <strong>{e}</strong></p>"
            f"<p>Please check:</p>"
            f"<ul>"
            f"  <li>Your <code>REDIS_URL</code> in <code>.env</code> or environment variables.</li>"
            f"  <li>Your <code>CACHES</code> configuration in <code>settings.py</code>.</li>"
            f"  <li>That your Upstash (or other Redis) instance is running and accessible.</li>"
            f"  <li>Your network connectivity and firewall rules (if applicable).</li>"
            f"</ul>"
        )
        return HttpResponseServerError(error_message)  # Return a 500 error
    except Exception as e:
        # Catch any other unexpected errors
        error_message = (
            f"<h1>Unexpected Error</h1>"
            f"<p style='color: red;'>An unexpected error occurred: <strong>{e}</strong></p>"
        )
        return HttpResponseServerError(error_message)
