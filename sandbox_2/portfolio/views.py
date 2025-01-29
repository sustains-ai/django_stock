from django.shortcuts import render, redirect
from .models import Portfolio, FundManager
from .forms import StockForm, PortfolioForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib import messages
import yfinance as yf
import riskfolio as rp
import matplotlib.pyplot as plt
import io
import base64
from django.shortcuts import render, get_object_or_404



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
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('portfolio_list')
    else:
        form = StockForm()
    return render(request, 'portfolio/add_stock.html', {'form': form})






def analyze_portfolio(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, fund_manager__user=request.user)
    stocks = portfolio.stocks.all()

    stock_data = []
    total_value = 0

    for stock in stocks:
        manual_price = stock.price
        live_price = stock.get_live_price()
        price = manual_price if manual_price else live_price

        if price:  # Only process stocks with valid prices
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

    print("DEBUG STOCK DATA:", stock_data)  # Print debug info

    return render(request, 'portfolio/analyze_portfolio.html', {
        'portfolio': portfolio,
        'stock_data': stock_data,
        'total_value': total_value,
    })







def delete_portfolio(request, portfolio_id):
    if request.method == "POST":
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)
        portfolio_name = portfolio.name
        portfolio.delete()
        messages.success(request, f'Portfolio "{portfolio_name}" has been deleted successfully.')
    return redirect('portfolio_list')