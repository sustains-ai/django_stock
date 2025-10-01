# Modern Views for Clean UI
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from .models import Portfolio, FundManager, Stock
from .decorators import fund_manager_required
from .utils import fetch_news_sentiment, global_open_closed_status
import json

@login_required
@fund_manager_required
def modern_dashboard(request):
    """Modern dashboard with clean UI"""
    try:
        fund_manager = request.user.fundmanager
        portfolios = Portfolio.objects.filter(fund_manager=fund_manager)
        
        # Calculate dashboard metrics from real data
        total_value = 0
        total_profit = 0
        profitable_portfolios = 0
        
        for portfolio in portfolios:
            # Calculate real portfolio value from stocks
            portfolio_value = 0
            portfolio_profit = 0
            
            for stock in portfolio.stocks.all():
                if stock.price and stock.quantity:
                    stock_value = stock.price * stock.quantity
                    portfolio_value += stock_value
                    # Calculate profit based on current vs initial price
                    if hasattr(stock, 'initial_price') and stock.initial_price:
                        profit = (stock.price - stock.initial_price) * stock.quantity
                        portfolio_profit += profit
            
            total_value += portfolio_value
            total_profit += portfolio_profit
            if portfolio_profit > 0:
                profitable_portfolios += 1
        
        avg_return = (total_profit / total_value * 100) if total_value > 0 else 0
        
        context = {
            'portfolios': portfolios,
            'total_value': f"{total_value:,.2f}",
            'total_profit': f"{total_profit:,.2f}",
            'portfolio_count': portfolios.count(),
            'profitable_portfolios': profitable_portfolios,
            'avg_return': f"{avg_return:.1f}",
        }
        
        return render(request, 'portfolio/modern_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return render(request, 'portfolio/modern_dashboard.html', {
            'portfolios': [],
            'total_value': "0.00",
            'total_profit': "0.00",
            'portfolio_count': 0,
            'profitable_portfolios': 0,
            'avg_return': "0.0",
        })

@login_required
@fund_manager_required
def modern_portfolio_list(request):
    """Modern portfolio list with clean UI"""
    try:
        fund_manager = request.user.fundmanager
        portfolios = Portfolio.objects.filter(fund_manager=fund_manager)
        
        return render(request, 'portfolio/modern_portfolio_list.html', {
            'portfolios': portfolios
        })
        
    except Exception as e:
        messages.error(request, f"Error loading portfolios: {str(e)}")
        return render(request, 'portfolio/modern_portfolio_list.html', {
            'portfolios': []
        })

def modern_login(request):
    """Modern login page with clean UI"""
    form = AuthenticationForm(data=request.POST or None)
    
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("/portfolio_list/")
    
    return render(request, 'portfolio/modern_login.html', {
        'form': form
    })

@login_required
@fund_manager_required
def modern_analytics(request):
    """Modern analytics page with clean charts"""
    try:
        fund_manager = request.user.fundmanager
        portfolios = Portfolio.objects.filter(fund_manager=fund_manager)
        
        # Sample analytics data
        analytics_data = {
            'performance_chart': {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'datasets': [{
                    'label': 'Portfolio Value',
                    'data': [10000, 10500, 11000, 10800, 11500, 12000],
                    'borderColor': '#fe5757',
                    'backgroundColor': 'rgba(254, 87, 87, 0.1)',
                    'fill': True
                }]
            },
            'risk_metrics': {
                'volatility': 12.5,
                'sharpe_ratio': 1.8,
                'max_drawdown': -5.2
            }
        }
        
        return render(request, 'portfolio/modern_analytics.html', {
            'portfolios': portfolios,
            'analytics_data': analytics_data
        })
        
    except Exception as e:
        messages.error(request, f"Error loading analytics: {str(e)}")
        return render(request, 'portfolio/modern_analytics.html', {
            'portfolios': [],
            'analytics_data': {}
        })

@login_required
@fund_manager_required
def modern_risk_analysis(request):
    """Modern risk analysis page"""
    try:
        fund_manager = request.user.fundmanager
        portfolios = Portfolio.objects.filter(fund_manager=fund_manager)
        
        # Sample risk data
        risk_data = {
            'overall_risk_score': 6.5,
            'risk_level': 'Moderate',
            'recommendations': [
                'Consider diversifying across more sectors',
                'Monitor high-volatility positions',
                'Review portfolio allocation monthly'
            ]
        }
        
        return render(request, 'portfolio/modern_risk.html', {
            'portfolios': portfolios,
            'risk_data': risk_data
        })
        
    except Exception as e:
        messages.error(request, f"Error loading risk analysis: {str(e)}")
        return render(request, 'portfolio/modern_risk.html', {
            'portfolios': [],
            'risk_data': {}
        })

def modern_logout(request):
    """Modern logout with redirect to login"""
    logout(request)
    return redirect('login')

@login_required
@fund_manager_required
def modern_analytics(request):
    """Modern analytics page with comprehensive data"""
    try:
        fund_manager = request.user.fundmanager
        portfolios = Portfolio.objects.filter(fund_manager=fund_manager)
        
        # Calculate analytics metrics
        total_portfolios = portfolios.count()
        total_stocks = sum(portfolio.stocks.count() for portfolio in portfolios)
        
        # Calculate real portfolio performance
        portfolio_performance = []
        for portfolio in portfolios:
            # Calculate real portfolio value
            portfolio_value = 0
            portfolio_profit = 0
            
            for stock in portfolio.stocks.all():
                if stock.price and stock.quantity:
                    stock_value = stock.price * stock.quantity
                    portfolio_value += stock_value
                    if hasattr(stock, 'initial_price') and stock.initial_price:
                        profit = (stock.price - stock.initial_price) * stock.quantity
                        portfolio_profit += profit
            
            # Calculate return percentage
            return_pct = (portfolio_profit / portfolio_value * 100) if portfolio_value > 0 else 0
            
            performance = {
                'portfolio': portfolio,
                'name': portfolio.name,
                'value': portfolio_value,
                'return': return_pct,
                'profit': portfolio_profit,
            }
            portfolio_performance.append(performance)
        
        # Calculate average return across all portfolios
        avg_return = 0
        if portfolio_performance:
            total_return = sum(perf['return'] for perf in portfolio_performance)
            avg_return = total_return / len(portfolio_performance)
        
        context = {
            'total_portfolios': total_portfolios,
            'total_stocks': total_stocks,
            'portfolio_performance': portfolio_performance,
            'avg_return': avg_return,
        }
        
        return render(request, 'portfolio/modern_analytics.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading analytics: {str(e)}")
        return render(request, 'portfolio/modern_analytics.html', {
            'total_portfolios': 0,
            'total_stocks': 0,
            'portfolio_performance': [],
        })

@login_required
@fund_manager_required
def modern_risk_analysis(request):
    """Modern risk analysis overview page"""
    try:
        fund_manager = request.user.fundmanager
        portfolios = Portfolio.objects.filter(fund_manager=fund_manager)
        
        # Calculate real risk metrics for each portfolio
        portfolio_risks = []
        for portfolio in portfolios:
            stock_count = portfolio.stocks.count()
            
            # Simple risk calculation based on number of stocks and diversification
            if stock_count == 0:
                risk_score = 0
                volatility = 0
            elif stock_count == 1:
                risk_score = 8  # High risk - no diversification
                volatility = 15
            elif stock_count <= 3:
                risk_score = 6  # Medium-high risk - limited diversification
                volatility = 12
            elif stock_count <= 10:
                risk_score = 4  # Medium risk - good diversification
                volatility = 8
            else:
                risk_score = 2  # Low risk - well diversified
                volatility = 5
            
            risk_data = {
                'portfolio': portfolio,
                'stock_count': stock_count,
                'risk_score': risk_score,
                'volatility': volatility,
            }
            portfolio_risks.append(risk_data)
        
        context = {
            'portfolios': portfolios,
            'portfolio_risks': portfolio_risks,
        }
        
        return render(request, 'portfolio/modern_risk.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading risk analysis: {str(e)}")
        return render(request, 'portfolio/modern_risk.html', {
            'portfolios': [],
            'portfolio_risks': [],
        })

@login_required
@fund_manager_required
def modern_settings(request):
    """Modern settings page"""
    try:
        fund_manager = request.user.fundmanager
        
        context = {
            'user': request.user,
            'fund_manager': fund_manager,
        }
        
        return render(request, 'portfolio/modern_settings.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading settings: {str(e)}")
        return render(request, 'portfolio/modern_settings.html', {
            'user': request.user,
            'fund_manager': None,
        })
