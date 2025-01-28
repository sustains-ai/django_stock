from django.shortcuts import render, redirect
from .models import Portfolio, FundManager
from .forms import StockForm, PortfolioForm
import yfinance as yf
import riskfolio as rp
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

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

    # Fetch stock symbols
    tickers = [stock.symbol for stock in stocks]
    if not tickers:
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'weights': {},
            'report': "No stocks available in the portfolio for analysis.",
        })

    # Fetch data from Yahoo Finance
    import yfinance as yf
    data = yf.download(tickers, period="1y", interval="1d")

    # Check if 'Adj Close' column exists
    if 'Adj Close' not in data:
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'weights': {},
            'report': "Failed to fetch adjusted close prices. Please check the stock symbols.",
        })

    # Extract the 'Adj Close' column and handle missing data
    data = data['Adj Close'].dropna(how='all')
    if data.empty:
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'weights': {},
            'report': "No valid stock data available for the selected portfolio.",
        })

    # Perform risk analysis with Riskfolio-Lib
    import riskfolio as rp
    model = rp.HCPortfolio(returns=data.pct_change().dropna())
    try:
        weights = model.optimization(model="Classic", rm="MV", rf=0, l=0)
        report = model.risk_contribution(weights)
    except ValueError as e:
        return render(request, 'portfolio/analyze_portfolio.html', {
            'portfolio': portfolio,
            'weights': {},
            'report': f"Error during analysis: {str(e)}",
        })

    return render(request, 'portfolio/analyze_portfolio.html', {
        'portfolio': portfolio,
        'weights': weights.to_dict(),
        'report': report.to_dict(),
    })
