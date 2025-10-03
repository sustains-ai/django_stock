from django.contrib import admin
from .models import (
    Institute, InstituteRole, FundManager, Portfolio, Stock, 
    UserProfile, InstituteSettings, UserInvitation
)


@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain', 'subscription_plan', 'is_active', 'created_at']
    list_filter = ['subscription_plan', 'is_active', 'created_at']
    search_fields = ['name', 'domain']
    fields = ['name', 'domain', 'logo', 'primary_color', 'subscription_plan', 'max_users', 'is_active']


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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'institute', 'get_role', 'is_active', 'created_at']
    list_filter = ['institute', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'institute__name']
    
    def get_role(self, obj):
        return obj.get_role()
    get_role.short_description = 'Role'


@admin.register(InstituteSettings)
class InstituteSettingsAdmin(admin.ModelAdmin):
    list_display = ['institute', 'allow_analytics', 'allow_risk_analysis', 'allow_ai_features']
    list_filter = ['allow_analytics', 'allow_risk_analysis', 'allow_ai_features']
    search_fields = ['institute__name']


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'institute', 'role', 'status', 'invited_by', 'created_at']
    list_filter = ['status', 'role', 'institute', 'created_at']
    search_fields = ['email', 'institute__name', 'invited_by__username']
    readonly_fields = ['token', 'created_at']
