from django.contrib import admin
from .models import Institute, InstituteRole, FundManager, Portfolio, Stock


@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(InstituteRole)
class InstituteRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'institute', 'role', 'created_at']
    list_filter = ['role', 'institute', 'created_at']
    search_fields = ['user__username', 'institute__name']


@admin.register(FundManager)
class FundManagerAdmin(admin.ModelAdmin):
    list_display = ['user', 'institute', 'is_active', 'created_at']
    list_filter = ['institute', 'is_active', 'created_at']
    search_fields = ['user__username', 'institute__name']


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['name', 'fund_manager', 'created_at']
    list_filter = ['fund_manager__institute', 'created_at']
    search_fields = ['name', 'fund_manager__user__username']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'portfolio', 'quantity', 'price']
    list_filter = ['portfolio__fund_manager__institute', 'portfolio']
    search_fields = ['symbol', 'name', 'portfolio__name']
