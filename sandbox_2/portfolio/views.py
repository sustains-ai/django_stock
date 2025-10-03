# Consolidated Views for Portfolio Management Application

from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseServerError
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.utils.timezone import now
from dotenv import load_dotenv
import os
import requests
import json
import pandas as pd
import numpy as np
import riskfolio as rp
from collections import defaultdict
from redis.exceptions import RedisError

from .models import Portfolio, FundManager, HistoricalStockData, Stock, InstituteRole, UserProfile, Institute, InstituteSettings, UserInvitation
from django.contrib.auth.models import User
from .forms import StockForm, PortfolioForm, UserCreationForm, UserInvitationForm, PasswordChangeForm, UserProfileForm
from .permissions import (
    fund_manager_required, 
    analyst_or_higher_required, 
    can_manage_portfolio, 
    can_view_portfolio,
    get_user_institutes,
    get_user_role,
    admin_required,
    manager_required,
    analyst_required,
    superadmin_required,
    is_superadmin
)
from .risk_analysis import perform_risk_analysis, calculate_risk_measures, calculate_portfolio_risk
from .utils import fetch_news_sentiment, global_open_closed_status, get_market_returns, get_treasury_yields, monte_carlo_portfolio_var_cvar
from .ai_agent import portfolio_risk_agent

load_dotenv()  # Ensures .env is loaded if not already




def test_view(request):
    return HttpResponse("Test view works!")


def admin_redirect(request):
    """Custom admin redirect - replaces Django admin"""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('superadmin_dashboard')
        else:
            return redirect('dashboard')
    else:
        return redirect('login')


@login_required
@superadmin_required
def onboard_company(request):
    """Onboard a new company with admin and manager users"""
    if request.method == 'POST':
        try:
            # Create the institute
            institute = Institute.objects.create(
                name=request.POST.get('company_name'),
                domain=request.POST.get('domain'),
                subscription_plan=request.POST.get('subscription_plan', 'basic'),
                max_users=int(request.POST.get('max_users', 10)),
                primary_color=request.POST.get('primary_color', '#007bff'),
                is_active=True
            )
            
            # Create institute settings
            InstituteSettings.objects.create(
                institute=institute,
                allow_analytics=True,
                allow_risk_analysis=True,
                allow_ai_features=True,
                max_portfolios_per_manager=50
            )
            
            # Create admin user
            admin_username = request.POST.get('admin_username')
            admin_email = request.POST.get('admin_email')
            admin_first_name = request.POST.get('admin_first_name')
            admin_last_name = request.POST.get('admin_last_name')
            admin_password = request.POST.get('admin_password')
            
            if admin_username and admin_email:
                admin_user = User.objects.create_user(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password,
                    first_name=admin_first_name,
                    last_name=admin_last_name
                )
                
                # Create admin profile and role
                UserProfile.objects.create(
                    user=admin_user,
                    institute=institute,
                    is_active=True
                )
                
                InstituteRole.objects.create(
                    user=admin_user,
                    institute=institute,
                    role='admin'
                )
            
            # Create manager user (optional)
            manager_username = request.POST.get('manager_username')
            manager_email = request.POST.get('manager_email')
            manager_first_name = request.POST.get('manager_first_name')
            manager_last_name = request.POST.get('manager_last_name')
            manager_password = request.POST.get('manager_password')
            
            if manager_username and manager_email and manager_password:
                manager_user = User.objects.create_user(
                    username=manager_username,
                    email=manager_email,
                    password=manager_password,
                    first_name=manager_first_name,
                    last_name=manager_last_name
                )
                
                # Create manager profile and role
                UserProfile.objects.create(
                    user=manager_user,
                    institute=institute,
                    is_active=True
                )
                
                InstituteRole.objects.create(
                    user=manager_user,
                    institute=institute,
                    role='manager'
                )
                
                # Create fund manager
                FundManager.objects.create(
                    user=manager_user,
                    institute=institute
                )
            
            messages.success(request, f"Company '{institute.name}' onboarded successfully!")
            return redirect('superadmin_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error onboarding company: {str(e)}")
            return redirect('superadmin_dashboard')
    
    return redirect('superadmin_dashboard')


# ===== DASHBOARD ROUTER =====
@login_required
def dashboard_router(request):
    """Route users to appropriate dashboard based on their role"""
    print(f"Dashboard router called for user: {request.user.username}")
    
    # Check if user is superadmin first
    if request.user.is_superuser:
        print("User is superuser, redirecting to superadmin dashboard")
        return redirect('superadmin_dashboard')
    
    try:
        user_profile = request.user.userprofile
        role = user_profile.get_role()
        print(f"User profile found, role: {role}")
        
        if role == 'admin':
            print("Redirecting to admin dashboard")
            return redirect('admin_dashboard')
        elif role == 'manager':
            print("Redirecting to manager dashboard")
            return redirect('manager_dashboard')
        elif role == 'analyst':
            print("Redirecting to analyst dashboard")
            return redirect('analyst_dashboard')
        else:
            print(f"Invalid role: {role}")
            messages.error(request, "No valid role assigned. Please contact your administrator.")
            return redirect('login')
    except UserProfile.DoesNotExist:
        print("UserProfile does not exist, creating default profile")
        # Handle users without profiles - create a default profile
        try:
            # Get the first institute (or create a default one)
            institute = Institute.objects.first()
            if not institute:
                print("Creating default institute")
                institute = Institute.objects.create(
                    name="Default Institute",
                    domain="default.com",
                    subscription_plan='basic',
                    max_users=10,
                    is_active=True
                )
                
                # Create institute settings
                InstituteSettings.objects.create(
                    institute=institute,
                    allow_analytics=True,
                    allow_risk_analysis=True,
                    allow_ai_features=True,
                    max_portfolios_per_manager=50
                )
            
            print(f"Creating user profile for {request.user.username}")
            # Create a default user profile with manager role
            user_profile = UserProfile.objects.create(
                user=request.user,
                institute=institute,
                is_active=True
            )
            
            # Create role
            InstituteRole.objects.create(
                user=request.user,
                institute=institute,
                role='manager'
            )
            
            # Create fund manager if needed
            if not FundManager.objects.filter(user=request.user).exists():
                FundManager.objects.create(
                    user=request.user,
                    institute=institute
                )
            
            print("User profile created successfully, redirecting to manager dashboard")
            messages.success(request, "Your account has been set up with default access. You can now use the system.")
            return redirect('manager_dashboard')
            
        except Exception as e:
            # Debug: Print the error to console
            print(f"Error creating user profile: {str(e)}")
            messages.error(request, f"Error setting up your account: {str(e)}. Please contact your administrator.")
            return redirect('login')


# ===== SUPERADMIN DASHBOARD =====
@login_required
@superadmin_required
def superadmin_dashboard(request):
    """System-wide dashboard for superadmins"""
    try:
        # System-wide metrics
        total_institutes = Institute.objects.count()
        total_users = User.objects.count()
        total_portfolios = Portfolio.objects.count()
        total_stocks = Stock.objects.count()
        
        # Calculate total system value
        total_value = 0
        for portfolio in Portfolio.objects.all():
            for stock in portfolio.stocks.all():
                if stock.price and stock.quantity:
                    total_value += stock.price * stock.quantity
        
        # Recent activity across all institutes
        recent_portfolios = Portfolio.objects.order_by('-created_at')[:10]
        recent_institutes = Institute.objects.order_by('-created_at')[:5]
        
        # Get all institutes with their stats
        institutes_with_stats = []
        for institute in Institute.objects.all():
            institute_stats = {
                'institute': institute,
                'user_count': UserProfile.objects.filter(institute=institute).count(),
                'portfolio_count': Portfolio.objects.filter(fund_manager__institute=institute).count(),
                'total_value': 0
            }
            
            # Calculate institute value
            for portfolio in Portfolio.objects.filter(fund_manager__institute=institute):
                for stock in portfolio.stocks.all():
                    if stock.price and stock.quantity:
                        institute_stats['total_value'] += stock.price * stock.quantity
            
            institutes_with_stats.append(institute_stats)
        
        context = {
            'total_institutes': total_institutes,
            'total_users': total_users,
            'total_portfolios': total_portfolios,
            'total_stocks': total_stocks,
            'total_value': f"{total_value:,.2f}",
            'recent_portfolios': recent_portfolios,
            'recent_institutes': recent_institutes,
            'institutes_with_stats': institutes_with_stats,
        }
        
        return render(request, 'portfolio/dashboards/superadmin_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading superadmin dashboard: {str(e)}")
        return redirect('login')


# ===== ADMIN DASHBOARD =====
@login_required
def admin_dashboard(request):
    """Company-wide dashboard for institute admins"""
    print(f"Admin dashboard called for user: {request.user.username}")
    
    try:
        user_profile = request.user.userprofile
        institute = user_profile.institute
        print(f"User profile found: {user_profile}, Institute: {institute}")
        
        # Company metrics
        total_users = UserProfile.objects.filter(institute=institute, is_active=True).count()
        active_managers = FundManager.objects.filter(institute=institute, is_active=True).count()
        total_portfolios = Portfolio.objects.filter(fund_manager__institute=institute).count()
        
        # Calculate total portfolio value
        total_value = 0
        for portfolio in Portfolio.objects.filter(fund_manager__institute=institute):
            for stock in portfolio.stocks.all():
                if stock.price and stock.quantity:
                    total_value += stock.price * stock.quantity
        
        # Recent activity with portfolio values
        recent_portfolios_qs = Portfolio.objects.filter(
            fund_manager__institute=institute
        ).order_by('-created_at')[:5]

        recent_portfolios = []
        for portfolio in recent_portfolios_qs:
            portfolio_value = 0
            for stock in portfolio.stocks.all():
                if stock.price and stock.quantity:
                    portfolio_value += stock.price * stock.quantity

            recent_portfolios.append({
                'portfolio': portfolio,
                'value': f"{portfolio_value:,.2f}"
            })
        
        # User management
        pending_invitations = UserInvitation.objects.filter(
            institute=institute, 
            status='pending'
        )
        
        # Get all users in the institute
        institute_users = UserProfile.objects.filter(institute=institute).select_related('user')
        
        context = {
            'institute': institute,
            'total_users': total_users,
            'active_managers': active_managers,
            'total_portfolios': total_portfolios,
            'total_value': f"{total_value:,.2f}",
            'recent_portfolios': recent_portfolios,
            'pending_invitations': pending_invitations,
            'institute_users': institute_users,
        }
        
        print("Rendering admin dashboard template")
        return render(request, 'portfolio/dashboards/admin_dashboard.html', context)
        
    except Exception as e:
        print(f"Error in admin dashboard: {str(e)}")
        messages.error(request, f"Error loading admin dashboard: {str(e)}")
        return redirect('login')


# ===== MANAGER DASHBOARD =====
@login_required
@manager_required
def manager_dashboard(request):
    """Enhanced dashboard for fund managers"""
    try:
        fund_manager = request.user.fundmanager
        portfolios = Portfolio.objects.filter(fund_manager=fund_manager)
        
        # Enhanced metrics
        total_value = 0
        total_profit = 0
        profitable_portfolios = 0
        
        for portfolio in portfolios:
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
        
        return render(request, 'portfolio/dashboards/manager_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading manager dashboard: {str(e)}")
        return redirect('login')


# ===== ANALYST DASHBOARD =====
@login_required
@analyst_required
def analyst_dashboard(request):
    """Read-only dashboard for analysts"""
    try:
        user_profile = request.user.userprofile
        institute = user_profile.institute
        
        # Institute-wide analytics
        all_portfolios = Portfolio.objects.filter(
            fund_manager__institute=institute
        )
        
        # Calculate institute-wide metrics
        total_value = 0
        total_portfolios = all_portfolios.count()
        total_stocks = 0
        
        for portfolio in all_portfolios:
            for stock in portfolio.stocks.all():
                if stock.price and stock.quantity:
                    total_value += stock.price * stock.quantity
                    total_stocks += 1
        
        # Recent portfolios
        recent_portfolios = all_portfolios.order_by('-created_at')[:10]
        
        # Top performing portfolios (mock data for now)
        top_portfolios = all_portfolios[:5]
        
        context = {
            'institute': institute,
            'total_value': f"{total_value:,.2f}",
            'total_portfolios': total_portfolios,
            'total_stocks': total_stocks,
            'recent_portfolios': recent_portfolios,
            'top_portfolios': top_portfolios,
        }
        
        return render(request, 'portfolio/dashboards/analyst_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading analyst dashboard: {str(e)}")
        return redirect('login')

def custom_login(request):
    from django.contrib.auth.forms import AuthenticationForm
    from django.contrib.auth import login
    from django.shortcuts import render, redirect
    
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            print(f"User {user.username} logged in successfully")
            
            # Provide role-specific feedback
            if user.is_superuser:
                messages.success(request, f"Welcome back, Superadmin! You have full system access.")
                print("User is superuser")
            else:
                try:
                    user_profile = user.userprofile
                    role = user_profile.get_role()
                    institute_name = user_profile.institute.name
                    print(f"User profile found: role={role}, institute={institute_name}")
                    
                    if role == 'admin':
                        messages.success(request, f"Welcome back, {user.get_full_name() or user.username}! You're logged in as an Admin of {institute_name}.")
                    elif role == 'manager':
                        messages.success(request, f"Welcome back, {user.get_full_name() or user.username}! You're logged in as a Fund Manager of {institute_name}.")
                    elif role == 'analyst':
                        messages.success(request, f"Welcome back, {user.get_full_name() or user.username}! You're logged in as an Analyst of {institute_name}.")
                    else:
                        messages.info(request, f"Welcome back, {user.get_full_name() or user.username}! Your role is being verified.")
                except UserProfile.DoesNotExist:
                    print("UserProfile does not exist")
                    messages.info(request, f"Welcome back, {user.get_full_name() or user.username}! Setting up your account...")
            
            print("Redirecting to dashboard")
            return redirect("dashboard")
    else:
        form = AuthenticationForm()
    
    return render(request, 'portfolio/login.html', {'form': form})




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
                messages.success(request, f'Portfolio "{portfolio.name}" created successfully! Now add some stocks to get started.')
                return redirect('add_stock', portfolio_id=portfolio.id)
            except FundManager.DoesNotExist:
                return render(request, 'portfolio/error.html', {'message': 'No FundManager associated with this user.'})
    else:
        form = PortfolioForm()
    return render(request, 'portfolio/add_portfolio.html', {'form': form})





@login_required
def add_stock(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)
    if request.method == "POST":
        form = StockForm(request.POST)
        print(f"Form data: {request.POST}")
        print(f"Form is valid: {form.is_valid()}")
        if form.is_valid():
            stock_data = form.save(commit=False)
            stock_data.portfolio = portfolio
            print(f"Stock data: {stock_data.symbol}, {stock_data.name}, {stock_data.quantity}, {stock_data.price}")

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
                print(f"Stock saved with ID: {stock_data.id}")
                print(f"Portfolio stocks count: {portfolio.stocks.count()}")
                messages.success(request, f"Added {stock_data.symbol} to {portfolio.name}")
                # Try to fetch historical data, but don't fail if it doesn't work
                try:
                    stock_data.fetch_and_store_historical_data()
                except Exception as e:
                    print(f"Historical data fetch failed: {e}")
                    # Don't show error to user, just log it
            return redirect("analyze_portfolio",portfolio_id=portfolio.id)
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, f"Invalid stock data. Please check the form. Errors: {form.errors}")
    else:
        form = StockForm()

    # Prepare stock data with calculated values
    stocks_with_values = []
    for stock in portfolio.stocks.all():
        total_value = (float(stock.price) * stock.quantity) if stock.price else 0
        stocks_with_values.append({
            'stock': stock,
            'total_value': total_value
        })

    return render(request, "portfolio/add_stock.html", {
        "form": form,
        "portfolio": portfolio,
        "stocks_with_values": stocks_with_values
    })



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
            'stocks': stocks,
            'stock_data': stock_data,
            'total_value': f"{total_value:.2f}",
            'total_return': "0.0",
            'risk_score': "6.5",
            'stock_count': stocks.count(),
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

    print(f"DEBUG: Total stocks in portfolio: {stocks.count()}")
    print(f"DEBUG: Stocks with historical data after dropna: {len(available_symbols)}")
    print(f"DEBUG: Available symbols: {available_symbols}")
    print(f"DEBUG: Daily prices shape: {daily_prices.shape}")

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
    print(f"DEBUG: Returns dataframe shape after pct_change: {X.shape}")
    print(f"DEBUG: Returns dataframe columns: {X.columns.tolist()}")

    if X.empty:
        messages.warning(request, "Not enough historical data to compute returns.")
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'stocks': stocks,
            'stock_data': stock_data,
            'total_value': f"{total_value:.2f}",
            'total_return': "0.0",
            'risk_score': "6.5",
            'stock_count': stocks.count(),
            'historical_data': json.dumps(historical_data),
            'portfolio_analysis': None,
            'risk_measures': {},
        })

    # Perform risk analysis
    portfolio_analysis = perform_risk_analysis(X)
    risk_measures = calculate_risk_measures(X, stock_symbols)

    # Calculate efficient frontier with 100 points for smoother curve
    from portfolio.risk_analysis import calculate_efficient_frontier
    efficient_frontier = calculate_efficient_frontier(X, num_points=100)

    if portfolio_analysis is None:
        messages.warning(request, "Portfolio optimization failed. Ensure enough price data is available.")
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'stocks': stocks,
            'stock_data': stock_data,
            'total_value': f"{total_value:.2f}",
            'total_return': "0.0",
            'risk_score': "6.5",
            'stock_count': stocks.count(),
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
        'stocks': stocks,
        'stock_data': stock_data,
        'total_value': f"{total_value:.2f}",
        'total_return': "0.0",
        'risk_score': "6.5",
        'stock_count': stocks.count(),
        'historical_data': json.dumps(historical_data or []),
        'portfolio_analysis': portfolio_analysis_json,
        'optimal_table': portfolio_analysis,
        'risk_measures': risk_measures,
        'portfolio_value_json': json.dumps(portfolio_value_json or []),
        'efficient_frontier': json.dumps(efficient_frontier) if efficient_frontier else None,
        'ai_answer': ai_answer,
        'timestamp': int(datetime.now().timestamp())
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
        return render(request, "portfolio/portfolio_risk.html", {
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
        return render(request, "portfolio/portfolio_risk.html", {
            "portfolio": portfolio,
        })

    # Compute daily returns
    X = price_data[available_symbols].pct_change().dropna()
    if X.empty:
        messages.warning(request, "Not enough historical data to compute returns.")
        return render(request, "portfolio/portfolio_risk.html", {
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
    
    # Create chart data for visualization
    chart_data = []
    layout = {}
    
    if measure == "std_dev":
        # Create a more informative standard deviation visualization
        chart_data = [{
            'x': ['Low Risk', 'Medium Risk', 'High Risk', 'Your Portfolio'],
            'y': [0.05, 0.15, 0.30, risk_value if risk_value is not None else 0],
            'type': 'bar',
            'name': 'Risk Levels',
            'marker': {
                'color': ['#28a745', '#ffc107', '#dc3545', '#fe5757'],
                'opacity': [0.7, 0.7, 0.7, 1.0]
            }
        }]
        layout = {
            'title': 'Portfolio Risk Comparison',
            'xaxis': {'title': 'Risk Categories'},
            'yaxis': {'title': 'Standard Deviation (%)'},
            'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50}
        }
    elif measure == "var":
        # Create a more meaningful VaR visualization with risk zones
        risk_value_display = risk_value if risk_value is not None else 0
        chart_data = [
            {
                'x': ['Conservative', 'Moderate', 'Aggressive', 'Your Portfolio'],
                'y': [0.01, 0.03, 0.05, risk_value_display],
                'type': 'bar',
                'name': 'VaR Comparison',
                'marker': {
                    'color': ['#28a745', '#ffc107', '#dc3545', '#fe5757'],
                    'opacity': [0.7, 0.7, 0.7, 1.0]
                }
            },
            {
                'x': ['Risk-Free Zone', 'Your VaR'],
                'y': [0, risk_value_display],
                'type': 'scatter',
                'mode': 'markers',
                'name': 'VaR Point',
                'marker': {
                    'color': ['#6c757d', '#fe5757'],
                    'size': [8, 15]
                }
            }
        ]
        layout = {
            'title': 'Value at Risk (95%) - Portfolio vs Benchmarks',
            'xaxis': {'title': 'Investment Strategies'},
            'yaxis': {'title': 'VaR (%)'},
            'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50}
        }
    elif measure == "cvar":
        # Create a comprehensive CVaR visualization
        risk_value_display = risk_value if risk_value is not None else 0
        chart_data = [
            {
                'x': ['Low Risk', 'Medium Risk', 'High Risk', 'Your Portfolio'],
                'y': [0.02, 0.04, 0.08, risk_value_display],
                'type': 'bar',
                'name': 'CVaR Comparison',
                'marker': {
                    'color': ['#28a745', '#ffc107', '#dc3545', '#fe5757'],
                    'opacity': [0.7, 0.7, 0.7, 1.0]
                }
            }
        ]
        layout = {
            'title': 'Conditional Value at Risk (95%) - Risk Assessment',
            'xaxis': {'title': 'Risk Categories'},
            'yaxis': {'title': 'CVaR (%)'},
            'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50}
        }
    
    return JsonResponse({
        'measure': measure,
        'value': risk_value,
        'chart_data': chart_data,
        'layout': layout
    })


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

    return render(request, "portfolio/analyze_portfolio.html", {
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
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)
    if request.method == "POST":
        question = request.POST.get("question")
        answer = portfolio_risk_agent(portfolio_id, question)
    return render(request, "portfolio/ask_ai.html", {"answer": answer, "portfolio": portfolio})


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


from django.http import JsonResponse
from .models import Portfolio, HistoricalStockData
from .utils import monte_carlo_portfolio_var_cvar
import pandas as pd
import numpy as np

import numpy as np
import pandas as pd
from django.http import JsonResponse
from .models import Portfolio, HistoricalStockData # Assuming these are correct
from .utils import monte_carlo_portfolio_var_cvar # Assuming this is correct

def monte_carlo_risk_view(request, portfolio_id):
    try:
        print(f"🔍 Starting Monte Carlo risk view for portfolio {portfolio_id}")
        portfolio = Portfolio.objects.get(id=portfolio_id)
        stocks = portfolio.stocks.all()

        price_data = []

        for stock in stocks:
            # Your existing logic for fetching and preparing price data
            records = HistoricalStockData.objects.filter(portfolio=portfolio, symbol=stock.symbol).order_by("date")
            if records.exists():
                df = pd.DataFrame(
                    [(r.date, r.adjusted_close) for r in records],
                    columns=["date", stock.symbol]
                ).set_index("date")
                price_data.append(df)
            else:
                print(f"⚠️ Skipping {stock.symbol} due to no data in portfolio {portfolio_id}") # Added portfolio_id for clarity

        if not price_data:
            print(f"❌ No price data found for any stock in portfolio {portfolio_id}") # Added portfolio_id
            # Consider status 400 for client-side correctable errors if appropriate,
            # or if no data means an issue with the portfolio setup.
            # For now, keeping 500 as per your original code.
            return JsonResponse({"error": "No price data found for any stock"}, status=500)

        combined_df = pd.concat(price_data, axis=1, join="inner").dropna()

        # Add a check for empty combined_df after join and dropna
        if combined_df.empty or len(combined_df) < 2: # Need at least 2 rows for shift(1)
            print(f"❌ Combined price data is insufficient after join/dropna for portfolio {portfolio_id}")
            return JsonResponse({"error": "Not enough overlapping/valid price data for analysis"}, status=500) # Or 400

        print(f"📊 Price Data (portfolio {portfolio_id}):\n", combined_df.head()) # Added portfolio_id

        log_returns = np.log(combined_df / combined_df.shift(1)).dropna()

        # Add a check for empty log_returns
        if log_returns.empty:
            print(f"❌ Log returns are empty for portfolio {portfolio_id}")
            return JsonResponse({"error": "Could not calculate log returns from available price data"}, status=500) # Or 400

        print(f"📈 Returns Data (portfolio {portfolio_id}):\n", log_returns.tail()) # Added portfolio_id

        # Ensure there's at least one column of returns for weighting
        if log_returns.shape[1] == 0:
            print(f"❌ No valid asset returns columns for portfolio {portfolio_id}")
            return JsonResponse({"error": "No valid asset returns to process"}, status=500) # Or 400

        weights = np.array([1.0 / log_returns.shape[1]] * log_returns.shape[1])
        portfolio_log_returns = log_returns.dot(weights)

        # Ensure portfolio_log_returns is not empty (e.g., if weights was empty, though unlikely with above check)
        if portfolio_log_returns.empty:
            print(f"❌ Portfolio log returns series is empty for portfolio {portfolio_id}")
            return JsonResponse({"error": "Could not calculate portfolio log returns"}, status=500) # Or 400


        # === ADDITIONS START HERE ===
        # Calculate mean and standard deviation of the portfolio log returns
        mean_return_raw = float(portfolio_log_returns.mean())
        std_dev_return_raw = float(portfolio_log_returns.std())

        # Get VaR and CVaR from your utils function (these are raw, e.g., -0.031)
        # Your function monte_carlo_portfolio_var_cvar already returns these
        var_raw, cvar_raw = monte_carlo_portfolio_var_cvar(portfolio_log_returns)

        # Convert all four values to percentages
        var_pct = var_raw * 100
        cvar_pct = cvar_raw * 100
        mean_return_pct = mean_return_raw * 100
        std_dev_return_pct = std_dev_return_raw * 100

        # Construct the JSON response with the keys JavaScript expects
        response_data = {
            "VaR_pct": round(var_pct, 4) if not np.isnan(var_pct) else None,
            "CVaR_pct": round(cvar_pct, 4) if not np.isnan(cvar_pct) else None,
            "mean_return_pct": round(mean_return_pct, 2) if not np.isnan(mean_return_pct) else None,
            "std_dev_return_pct": round(std_dev_return_pct, 2) if not np.isnan(std_dev_return_pct) else None,
        }
        # === ADDITIONS END HERE ===

        # Print the data being sent for debugging
        print(f"✅ monte_carlo_risk_view for portfolio {portfolio_id} sending data: {response_data}")
        return JsonResponse(response_data) # Return the new response_data

    # Your existing exception handling
    except Portfolio.DoesNotExist: # Specific exception first
        print(f"❌ Portfolio with ID {portfolio_id} not found.")
        return JsonResponse({"error": "Portfolio not found"}, status=404)
    except Exception as e:
        print(f"❌ Exception occurred in monte_carlo_risk_view for portfolio {portfolio_id}: {e}")
        import traceback # Import traceback here for more detailed error logging
        traceback.print_exc() # This will print the full Python traceback to your console
        return JsonResponse({"error": str(e)}, status=500)





from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Portfolio, Stock, HistoricalStockData
import numpy as np
from collections import defaultdict
from .utils import get_market_returns
from .utils import get_treasury_yields



def performance_stats(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)
    stocks = Stock.objects.filter(portfolio=portfolio)

    if not stocks.exists():
        return JsonResponse({"error": "No stocks in this portfolio."}, status=404)

    # --- Total Buying Price ---
    total_buying_price = sum((stock.price or 0) * stock.quantity for stock in stocks)

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
    historical_data = HistoricalStockData.objects.filter(portfolio=portfolio).order_by("date")
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
        daily_values[row.date] += row.adjusted_close  # Already portfolio-linked

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

    sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if len(returns) > 1 else None
    cumulative_return = (values[-1] - values[0]) / values[0] if values[0] else None

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


import logging
from django.http import JsonResponse
from .utils import get_treasury_yields

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

from django.http import HttpResponse, HttpResponseServerError
from django.core.cache import cache
from redis.exceptions import RedisError # To catch potential Redis connection issues

def test_redis_cache(request):
    key = "my_django_test_key"  # Let's use a slightly more descriptive key
    value_to_set = "Hello from Django, cached in Redis!"
    html_response = "<h1>Redis Cache Test</h1>"

    try:
        # 1. Set a value in the cache
        cache.set(key, value_to_set, timeout=60) # Cache for 60 seconds
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
        return HttpResponseServerError(error_message) # Return a 500 error
    except Exception as e:
        # Catch any other unexpected errors
        error_message = (
            f"<h1>Unexpected Error</h1>"
            f"<p style='color: red;'>An unexpected error occurred: <strong>{e}</strong></p>"
        )
        return HttpResponseServerError(error_message)


# Modern Views for Clean UI
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
        
        return render(request, 'portfolio/dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return render(request, 'portfolio/dashboard.html', {
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
        
        return render(request, 'portfolio/portfolio_list.html', {
            'portfolios': portfolios
        })
        
    except Exception as e:
        messages.error(request, f"Error loading portfolios: {str(e)}")
        return render(request, 'portfolio/portfolio_list.html', {
            'portfolios': []
        })


def modern_login(request):
    """Modern login page with clean UI"""
    form = AuthenticationForm(data=request.POST or None)
    
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("/dashboard/")
    
    return render(request, 'portfolio/login.html', {
        'form': form
    })


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
        
        return render(request, 'portfolio/analytics.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading analytics: {str(e)}")
        return render(request, 'portfolio/analytics.html', {
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
        
        return render(request, 'portfolio/risk.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading risk analysis: {str(e)}")
        return render(request, 'portfolio/risk.html', {
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
        
        return render(request, 'portfolio/settings.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading settings: {str(e)}")
        return render(request, 'portfolio/settings.html', {
            'user': request.user,
            'fund_manager': None,
        })


def modern_logout(request):
    """Modern logout with redirect to login"""
    logout(request)
    return redirect('login')


# Additional utility views
@login_required
def dashboard_redirect(request):
    """
    Redirect to dashboard view.
    """
    return redirect('dashboard')


# User Management Views
@login_required
@admin_required
def create_user(request):
    """Create a new user (Admin only)"""
    try:
        user_profile = request.user.userprofile
        institute = user_profile.institute
        
        if request.method == 'POST':
            form = UserCreationForm(request.POST, institute=institute)
            if form.is_valid():
                # Create the user
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['temporary_password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name']
                )
                
                # Create user profile
                UserProfile.objects.create(
                    user=user,
                    institute=institute,
                    is_active=True
                )
                
                # Create role
                InstituteRole.objects.create(
                    user=user,
                    institute=institute,
                    role=form.cleaned_data['role']
                )
                
                # Create fund manager if role is manager
                if form.cleaned_data['role'] == 'manager':
                    FundManager.objects.create(
                        user=user,
                        institute=institute
                    )
                
                messages.success(request, f"User {user.username} created successfully with {form.cleaned_data['role']} role.")
                return redirect('admin_dashboard')
        else:
            form = UserCreationForm(institute=institute)
        
        context = {
            'form': form,
            'institute': institute
        }
        return render(request, 'portfolio/admin/create_user.html', context)
        
    except Exception as e:
        messages.error(request, f"Error creating user: {str(e)}")
        return redirect('admin_dashboard')


@login_required
@admin_required
def invite_user(request):
    """Send user invitation (Admin only)"""
    try:
        user_profile = request.user.userprofile
        institute = user_profile.institute
        
        if request.method == 'POST':
            form = UserInvitationForm(request.POST, institute=institute)
            if form.is_valid():
                # Create invitation
                import uuid
                from django.utils import timezone
                from datetime import timedelta
                
                invitation = UserInvitation.objects.create(
                    institute=institute,
                    email=form.cleaned_data['email'],
                    role=form.cleaned_data['role'],
                    invited_by=request.user,
                    token=str(uuid.uuid4()),
                    expires_at=timezone.now() + timedelta(days=7)
                )
                
                # TODO: Send email invitation
                # For now, just show the invitation link
                invitation_url = f"{request.build_absolute_uri('/')}accept-invitation/{invitation.token}/"
                
                messages.success(request, f"Invitation sent to {form.cleaned_data['email']}. Invitation link: {invitation_url}")
                return redirect('admin_dashboard')
        else:
            form = UserInvitationForm(institute=institute)
        
        context = {
            'form': form,
            'institute': institute
        }
        return render(request, 'portfolio/admin/invite_user.html', context)
        
    except Exception as e:
        messages.error(request, f"Error sending invitation: {str(e)}")
        return redirect('admin_dashboard')


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            
            # Re-login the user
            from django.contrib.auth import login
            login(request, user)
            
            messages.success(request, "Your password has been changed successfully.")
            return redirect('dashboard')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form
    }
    return render(request, 'portfolio/user/change_password.html', context)


@login_required
def user_profile(request):
    """View and edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    try:
        user_profile = request.user.userprofile
        role = user_profile.get_role()
        institute = user_profile.institute
    except UserProfile.DoesNotExist:
        role = None
        institute = None
    
    context = {
        'form': form,
        'user_profile': user_profile if 'user_profile' in locals() else None,
        'role': role,
        'institute': institute
    }
    return render(request, 'portfolio/user/profile.html', context)


@login_required
@admin_required
def manage_users(request):
    """Manage users in the institute (Admin only)"""
    try:
        user_profile = request.user.userprofile
        institute = user_profile.institute
        
        # Get all users in the institute
        users = UserProfile.objects.filter(institute=institute).select_related('user')
        
        # Get pending invitations
        invitations = UserInvitation.objects.filter(institute=institute, status='pending')
        
        context = {
            'users': users,
            'invitations': invitations,
            'institute': institute
        }
        return render(request, 'portfolio/admin/manage_users.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading users: {str(e)}")
        return redirect('admin_dashboard')


def accept_invitation(request, token):
    """Accept user invitation"""
    try:
        invitation = UserInvitation.objects.get(token=token, status='pending')
        
        if invitation.is_expired():
            messages.error(request, "This invitation has expired.")
            return redirect('login')
        
        if request.method == 'POST':
            # Create user account
            form = UserCreationForm(request.POST, institute=invitation.institute)
            if form.is_valid():
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=invitation.email,
                    password=form.cleaned_data['temporary_password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name']
                )
                
                # Accept invitation
                invitation.accept(user)
                
                messages.success(request, "Account created successfully! You can now log in.")
                return redirect('login')
        else:
            form = UserCreationForm(institute=invitation.institute)
            # Pre-fill email
            form.fields['email'].initial = invitation.email
            form.fields['email'].widget.attrs['readonly'] = True
        
        context = {
            'form': form,
            'invitation': invitation
        }
        return render(request, 'portfolio/user/accept_invitation.html', context)
        
    except UserInvitation.DoesNotExist:
        messages.error(request, "Invalid invitation link.")
        return redirect('login')
    except Exception as e:
        messages.error(request, f"Error accepting invitation: {str(e)}")
        return redirect('login')