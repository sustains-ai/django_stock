from django.http import JsonResponse
from portfolio.models import Portfolio, Stock
from .utils import get_esg_scores_for_portfolio
from django.core.cache import cache




def esg_analytics_view(request, portfolio_id):
    return render(request, 'advanced_analytics/esg_analytics.html', {'portfolio_id': portfolio_id})

def advanced_risk(request, portfolio_id):
    return render(request, "advanced_analytics/advanced_risk.html", {"portfolio_id": portfolio_id})

def ml_strategies(request, portfolio_id):
    return render(request, "advanced_analytics/ml_strategies.html", {"portfolio_id": portfolio_id})

def stress_testing(request, portfolio_id):
    return render(request, "advanced_analytics/stress_testing.html", {"portfolio_id": portfolio_id})

def backtesting(request, portfolio_id):
    return render(request, "advanced_analytics/backtesting.html", {"portfolio_id": portfolio_id})

def rebalance_insights(request, portfolio_id):
    return render(request, "advanced_analytics/rebalance_insights.html", {"portfolio_id": portfolio_id})

def generate_report(request, portfolio_id):
    return render(request, "advanced_analytics/report.html", {"portfolio_id": portfolio_id})
from django.shortcuts import render



# Create your views here.

import json
from django.core.cache import cache
from django.http import JsonResponse
from portfolio.models import Stock
from .utils import get_esg_scores_for_portfolio

def fetch_esg_scores(request, portfolio_id):
    cache_key = f"esg_scores_{portfolio_id}"

    # Try to get ESG scores from cache
    cached_data = cache.get(cache_key)
    if cached_data:
        print(f"✅ Cache HIT for {cache_key}")
        return JsonResponse({"esg_scores": cached_data})

    print(f"🟡 Cache MISS for {cache_key}. Fetching fresh ESG data...")
    try:
        symbols = list(Stock.objects.filter(portfolio_id=portfolio_id).values_list('symbol', flat=True))
        esg_data = get_esg_scores_for_portfolio(symbols)

        if not esg_data:
            return JsonResponse({"esg_scores": []})  # or optionally send a message too

        # Cache ESG data for 90 days (quarterly updates)
        cache.set(cache_key, esg_data, timeout=60 * 60 * 24 * 90)
        print(f"✅ ESG scores cached under key {cache_key}")
        return JsonResponse({"esg_scores": esg_data})

    except Exception as e:
        print(f"❌ Error in fetch_esg_scores: {e}")
        return JsonResponse({"error": str(e)}, status=500)
