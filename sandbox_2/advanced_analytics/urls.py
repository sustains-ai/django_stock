from django.urls import path
from . import views

app_name = 'advanced_analytics'

urlpatterns = [
    # Main pages
    path('esg/<int:portfolio_id>/', views.esg_analytics_view, name='esg_analytics'),
    path('risk/<int:portfolio_id>/', views.advanced_risk, name='advanced_risk'),
    path('ml/<int:portfolio_id>/', views.ml_strategies, name='ml_strategies'),
    path('stress/<int:portfolio_id>/', views.stress_testing, name='stress_testing'),
    path('backtest/<int:portfolio_id>/', views.backtesting, name='backtesting'),
    path('rebalance/<int:portfolio_id>/', views.rebalance_insights, name='rebalance_insights'),
    path('report/<int:portfolio_id>/', views.generate_report, name='generate_report'),

    # API endpoints
    path('api/fetch-esg-scores/<int:portfolio_id>/', views.fetch_esg_scores, name='fetch_esg_scores'),
    path('api/fetch-stress-test/<int:portfolio_id>/', views.fetch_stress_test_results, name='fetch_stress_test'),
    path('api/fetch-ml-predictions/<int:portfolio_id>/', views.fetch_ml_predictions, name='fetch_ml_predictions'),
    path('api/fetch-backtest/<int:portfolio_id>/', views.fetch_backtest_results, name='fetch_backtest'),
]
