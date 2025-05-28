from django.shortcuts import render

def esg_analytics(request, portfolio_id):
    return render(request, "advanced_analytics/esg_analytics.html", {"portfolio_id": portfolio_id})

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
