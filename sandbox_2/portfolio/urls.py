from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('about/', views.about, name='about'),
    path('portfolio_list/', views.portfolio_list, name='portfolio_list'),
    path('add_portfolio/', views.add_portfolio, name='add_portfolio'),
    path('add_stock/', views.add_stock, name='add_stock'),
    path('analyze/<int:portfolio_id>/', views.analyze_portfolio, name='analyze_portfolio'),
    path('delete_portfolio/<int:portfolio_id>/', views.delete_portfolio, name='delete_portfolio'),
]
