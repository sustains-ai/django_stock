from django.urls import path
from . import views

urlpatterns = [
    path('esg/<int:portfolio_id>/', views.esg_analytics_view, name='esg_analytics'),
    path('fetch-esg-scores/<int:portfolio_id>/', views.fetch_esg_scores, name='fetch_esg_scores'),

    path('risk/<int:portfolio_id>/', views.advanced_risk, name='advanced_risk'),
    path('ml/<int:portfolio_id>/', views.ml_strategies, name='ml_strategies'),
    path('stress/<int:portfolio_id>/', views.stress_testing, name='stress_testing'),
    path('backtest/<int:portfolio_id>/', views.backtesting, name='backtesting'),
    path('rebalance/<int:portfolio_id>/', views.rebalance_insights, name='rebalance_insights'),
    path('report/<int:portfolio_id>/', views.generate_report, name='generate_report'),
]
