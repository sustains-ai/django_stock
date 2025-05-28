from django.urls import path
from . import views

urlpatterns = [
    path('esg/<int:portfolio_id>/', views.esg_analytics, name='esg_analytics'),
    path('risk/<int:portfolio_id>/', views.advanced_risk, name='advanced_risk'),
    path('ml/<int:portfolio_id>/', views.ml_strategies, name='ml_strategies'),
    path('stress/<int:portfolio_id>/', views.stress_testing, name='stress_testing'),
    path('backtest/<int:portfolio_id>/', views.backtesting, name='backtesting'),
    path('rebalance/<int:portfolio_id>/', views.rebalance_insights, name='rebalance_insights'),
    path('report/<int:portfolio_id>/', views.generate_report, name='generate_report'),
]
