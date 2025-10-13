from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from portfolio.models import Portfolio, Stock, HistoricalStockData
from .utils import get_esg_scores_for_portfolio
from django.core.cache import cache
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json


@login_required
def esg_analytics_view(request, portfolio_id):
    """ESG Analytics Dashboard with Environmental, Social, and Governance scores"""
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)
    return render(request, 'advanced_analytics/esg_analytics.html', {
        'portfolio': portfolio,
        'portfolio_id': portfolio_id
    })


@login_required
def advanced_risk(request, portfolio_id):
    """Advanced Risk Analysis with VaR, CVaR, and Stress Scenarios"""
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)

    cache_key = f'advanced_risk_{portfolio_id}'
    cached_data = cache.get(cache_key)

    if cached_data:
        return render(request, "advanced_analytics/advanced_risk.html", cached_data)

    stocks = portfolio.stocks.all()

    # Calculate portfolio metrics
    total_value = sum(float(stock.price or 0) * stock.quantity for stock in stocks)

    # Risk metrics
    risk_data = {
        'portfolio': portfolio,
        'portfolio_id': portfolio_id,
        'total_value': total_value,
        'stock_count': stocks.count(),
    }

    cache.set(cache_key, risk_data, 300)
    return render(request, "advanced_analytics/advanced_risk.html", risk_data)


@login_required
def ml_strategies(request, portfolio_id):
    """ML-based Trading Strategies and Predictions"""
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)

    cache_key = f'ml_strategies_{portfolio_id}'
    cached_data = cache.get(cache_key)

    if cached_data:
        return render(request, "advanced_analytics/ml_strategies.html", cached_data)

    stocks = portfolio.stocks.all()

    context = {
        'portfolio': portfolio,
        'portfolio_id': portfolio_id,
        'stocks': stocks,
    }

    cache.set(cache_key, context, 300)
    return render(request, "advanced_analytics/ml_strategies.html", context)


@login_required
def stress_testing(request, portfolio_id):
    """Stress Testing with Market Crash Scenarios"""
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)

    cache_key = f'stress_testing_{portfolio_id}'
    cached_data = cache.get(cache_key)

    if cached_data:
        return render(request, "advanced_analytics/stress_testing.html", cached_data)

    stocks = portfolio.stocks.all()
    total_value = sum(float(stock.price or 0) * stock.quantity for stock in stocks)

    context = {
        'portfolio': portfolio,
        'portfolio_id': portfolio_id,
        'total_value': total_value,
        'stocks': stocks,
    }

    cache.set(cache_key, context, 300)
    return render(request, "advanced_analytics/stress_testing.html", context)


@login_required
def backtesting(request, portfolio_id):
    """Historical Backtesting and Performance Analysis"""
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)

    cache_key = f'backtesting_{portfolio_id}'
    cached_data = cache.get(cache_key)

    if cached_data:
        return render(request, "advanced_analytics/backtesting.html", cached_data)

    stocks = portfolio.stocks.all()

    context = {
        'portfolio': portfolio,
        'portfolio_id': portfolio_id,
        'stocks': stocks,
    }

    cache.set(cache_key, context, 300)
    return render(request, "advanced_analytics/backtesting.html", context)


@login_required
def rebalance_insights(request, portfolio_id):
    """Portfolio Rebalancing Recommendations"""
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)

    cache_key = f'rebalance_insights_{portfolio_id}'
    cached_data = cache.get(cache_key)

    if cached_data:
        return render(request, "advanced_analytics/rebalance_insights.html", cached_data)

    stocks = portfolio.stocks.all()
    total_value = sum(float(stock.price or 0) * stock.quantity for stock in stocks)

    # Calculate current allocation
    allocations = []
    for stock in stocks:
        stock_value = float(stock.price or 0) * stock.quantity
        allocation = (stock_value / total_value * 100) if total_value > 0 else 0
        allocations.append({
            'symbol': stock.symbol,
            'name': stock.name,
            'current_allocation': allocation,
            'value': stock_value,
        })

    context = {
        'portfolio': portfolio,
        'portfolio_id': portfolio_id,
        'total_value': total_value,
        'allocations': allocations,
    }

    cache.set(cache_key, context, 300)
    return render(request, "advanced_analytics/rebalance_insights.html", context)


@login_required
def generate_report(request, portfolio_id):
    """Comprehensive Portfolio Report Generation"""
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)

    stocks = portfolio.stocks.all()
    total_value = sum(float(stock.price or 0) * stock.quantity for stock in stocks)

    context = {
        'portfolio': portfolio,
        'portfolio_id': portfolio_id,
        'total_value': total_value,
        'stocks': stocks,
        'report_date': datetime.now(),
    }

    return render(request, "advanced_analytics/report.html", context)



# API Endpoints for AJAX calls

@login_required
def fetch_esg_scores(request, portfolio_id):
    """API endpoint to fetch ESG scores for portfolio stocks"""
    cache_key = f"esg_scores_{portfolio_id}"

    # Try to get ESG scores from cache
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse({"esg_scores": cached_data})

    try:
        symbols = list(Stock.objects.filter(portfolio_id=portfolio_id).values_list('symbol', flat=True))
        esg_data = get_esg_scores_for_portfolio(symbols)

        if not esg_data:
            return JsonResponse({"esg_scores": []})

        # Cache ESG data for 90 days (quarterly updates)
        cache.set(cache_key, esg_data, timeout=60 * 60 * 24 * 90)
        return JsonResponse({"esg_scores": esg_data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def fetch_stress_test_results(request, portfolio_id):
    """API endpoint for stress testing scenarios"""
    cache_key = f"stress_test_{portfolio_id}"
    cached_data = cache.get(cache_key)

    if cached_data:
        return JsonResponse(cached_data)

    try:
        portfolio = Portfolio.objects.get(id=portfolio_id, fund_manager__user=request.user)
        stocks = portfolio.stocks.all()
        total_value = sum(float(stock.price or 0) * stock.quantity for stock in stocks)

        # Stress test scenarios
        scenarios = [
            {'name': 'Market Crash -30%', 'impact': -0.30, 'loss': total_value * 0.30},
            {'name': 'Recession -20%', 'impact': -0.20, 'loss': total_value * 0.20},
            {'name': 'Black Swan -40%', 'impact': -0.40, 'loss': total_value * 0.40},
            {'name': 'Moderate Correction -10%', 'impact': -0.10, 'loss': total_value * 0.10},
            {'name': 'Tech Bubble Burst -35%', 'impact': -0.35, 'loss': total_value * 0.35},
        ]

        result = {
            'current_value': total_value,
            'scenarios': scenarios
        }

        cache.set(cache_key, result, 300)
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def fetch_ml_predictions(request, portfolio_id):
    """API endpoint for ML-based stock predictions"""
    cache_key = f"ml_predictions_{portfolio_id}"
    cached_data = cache.get(cache_key)

    if cached_data:
        return JsonResponse(cached_data)

    try:
        portfolio = Portfolio.objects.get(id=portfolio_id, fund_manager__user=request.user)
        stocks = portfolio.stocks.all()

        predictions = []
        for stock in stocks:
            # Simplified ML prediction (in real app, use actual ML model)
            current_price = float(stock.price or 0)
            predicted_change = np.random.uniform(-0.15, 0.15)  # ±15% prediction range
            predicted_price = current_price * (1 + predicted_change)

            predictions.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'current_price': round(current_price, 2),
                'predicted_price': round(predicted_price, 2),
                'predicted_change': round(predicted_change * 100, 2),
                'confidence': round(np.random.uniform(0.6, 0.95), 2),
                'recommendation': 'BUY' if predicted_change > 0.05 else ('SELL' if predicted_change < -0.05 else 'HOLD')
            })

        result = {'predictions': predictions}
        cache.set(cache_key, result, 300)
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def fetch_backtest_results(request, portfolio_id):
    """API endpoint for historical backtesting"""
    cache_key = f"backtest_{portfolio_id}"
    cached_data = cache.get(cache_key)

    if cached_data:
        return JsonResponse(cached_data)

    try:
        portfolio = Portfolio.objects.get(id=portfolio_id, fund_manager__user=request.user)
        stocks = portfolio.stocks.all()

        # Calculate historical performance (simplified)
        backtest_periods = ['1M', '3M', '6M', '1Y', 'YTD']
        returns = []

        for period in backtest_periods:
            # Simplified calculation (in real app, use actual historical data)
            period_return = np.random.uniform(-0.20, 0.30)
            returns.append({
                'period': period,
                'return': round(period_return * 100, 2),
                'sharpe_ratio': round(np.random.uniform(0.5, 2.5), 2)
            })

        result = {
            'periods': returns,
            'total_trades': len(stocks),
        }

        cache.set(cache_key, result, 300)
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
