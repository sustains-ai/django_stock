from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    # path('about/', views.about, name='about'),
    path('portfolio_list/', views.portfolio_list, name='portfolio_list'),
    path('add_portfolio/', views.add_portfolio, name='add_portfolio'),
    path('add_stock/', views.add_stock, name='add_stock'),
    path('portfolio/<int:portfolio_id>/delete-stock/<str:symbol>/',
         views.delete_stock, name='delete_stock'),

    path(
        'analyze/<int:portfolio_id>/',
        views.analyze_portfolio,
        name='analyze_portfolio'),
    path(
        'delete_portfolio/<int:portfolio_id>/',
        views.delete_portfolio,
        name='delete_portfolio'),
    path("load-risk-measure/<int:portfolio_id>/<str:measure>/",
         views.load_risk_measure, name="load_risk_measure"),
    path(
        'portfolio/<int:portfolio_id>/risk/',
        views.portfolio_risk,
        name='portfolio_risk'),
    path('api/market-status/', views.market_status_view, name='market_status'),
    path("ask-ai/<int:portfolio_id>/", views.ask_ai_view, name="ask_ai"),
    path('analyze/<int:portfolio_id>/fetch-news/',
         views.fetch_news_view, name='fetch_news'),
    path(
        'fetch-currency-rates/<int:portfolio_id>/',
        views.fetch_currency_rates,
        name='fetch_currency_rates'),
    path(
        'fetch-treasury-yield/<int:portfolio_id>/',
        views.fetch_treasury_yield_view,
        name='fetch_treasury_yield'),
    path(
        'monte-carlo-risk/<int:portfolio_id>/',
        views.monte_carlo_risk_view,
        name='monte_carlo_risk'),
    path("api/portfolio/<int:portfolio_id>/performance-stats/",
         views.performance_stats, name="performance-stats"),
    path(
        'all-yield-data/<int:portfolio_id>/',
        views.get_all_yield_data,
        name='all_yield_data'),
    path("test-redis/", views.test_redis_cache),











    # login and logout
    path('', views.custom_login, name='login'),
    path(
        'logout/',
        auth_views.LogoutView.as_view(
            next_page='login'),
        name='logout'),


]
