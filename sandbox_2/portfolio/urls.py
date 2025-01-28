from django.urls import path
from . import views

urlpatterns = [
    path('', views.portfolio_list, name='portfolio_list'),
    path('add_portfolio/', views.add_portfolio, name='add_portfolio'),
    path('add_stock/', views.add_stock, name='add_stock'),
    path('analyze/<int:portfolio_id>/', views.analyze_portfolio, name='analyze_portfolio'),
]
