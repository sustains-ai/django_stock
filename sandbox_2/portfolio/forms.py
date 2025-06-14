from django import forms
from .models import Stock, Portfolio


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['portfolio', 'symbol', 'name', 'quantity', 'price']


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ['name', 'description']
