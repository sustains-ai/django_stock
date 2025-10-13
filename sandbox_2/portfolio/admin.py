from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import (
    Institute, InstituteRole, FundManager, Portfolio, Stock,
    UserProfile, InstituteSettings, UserInvitation, HistoricalStockData
)

# Simple customization of the default Django Admin Site
admin.site.site_header = 'Sandbox Administration'
admin.site.site_title = 'Sandbox Admin Portal'
admin.site.index_title = 'Welcome to Sandbox Admin Panel'


# Inline for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile (REQUIRED)'
    fk_name = 'user'
    fields = ['institute', 'is_active']
    min_num = 1  # Require at least 1
    max_num = 1  # Allow only 1
    extra = 1


# Inline for InstituteRole
class InstituteRoleInline(admin.TabularInline):
    model = InstituteRole
    verbose_name_plural = 'Institute Role (REQUIRED - If role is Manager, also add Fund Manager below)'
    fk_name = 'user'
    fields = ['institute', 'role']
    min_num = 1  # Require at least 1
    extra = 1


# Inline for FundManager
class FundManagerInline(admin.StackedInline):
    model = FundManager
    can_delete = True
    verbose_name_plural = 'Fund Manager (REQUIRED if role is Manager above)'
    fk_name = 'user'
    fields = ['institute', 'is_active']
    extra = 1  # Show 1 empty form


# Custom User Admin for Multi-Tenancy
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    list_per_page = 50
    date_hierarchy = 'date_joined'

    # Add inlines to show UserProfile, InstituteRole, and FundManager forms
    inlines = [UserProfileInline, InstituteRoleInline, FundManagerInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('username', 'password', 'email', 'first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
        }),
    )
    readonly_fields = ['last_login', 'date_joined']
    filter_horizontal = ['groups', 'user_permissions']

    def save_related(self, request, form, formsets, change):
        """Custom validation to ensure FundManager is created for manager role"""
        super().save_related(request, form, formsets, change)

        user = form.instance

        # Check if user has manager role
        has_manager_role = InstituteRole.objects.filter(user=user, role='manager').exists()
        has_fund_manager = FundManager.objects.filter(user=user).exists()

        if has_manager_role and not has_fund_manager:
            from django.contrib import messages
            messages.error(
                request,
                f"ERROR: User '{user.username}' has 'manager' role but no Fund Manager entry. "
                "Please add a Fund Manager entry or change the role."
            )
        elif has_manager_role and has_fund_manager:
            from django.contrib import messages
            messages.success(
                request,
                f"User '{user.username}' successfully created with manager role and fund manager access."
            )


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain', 'subscription_plan', 'is_active', 'max_users', 'created_at']
    list_filter = ['subscription_plan', 'is_active', 'created_at']
    search_fields = ['name', 'domain']
    fields = ['name', 'domain', 'logo', 'primary_color', 'subscription_plan', 'max_users', 'is_active']
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['activate_institutes', 'deactivate_institutes']
    ordering = ['-created_at']

    def activate_institutes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} institute(s) activated successfully.")
    activate_institutes.short_description = "Activate selected institutes"

    def deactivate_institutes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} institute(s) deactivated successfully.")
    deactivate_institutes.short_description = "Deactivate selected institutes"


@admin.register(InstituteRole)
class InstituteRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'institute', 'role', 'created_at']
    list_filter = ['role', 'institute', 'created_at']
    search_fields = ['user__username', 'user__email', 'institute__name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    # Removed autocomplete_fields to use standard dropdowns
    raw_id_fields = ['user', 'institute']


@admin.register(FundManager)
class FundManagerAdmin(admin.ModelAdmin):
    list_display = ['user', 'institute', 'is_active', 'portfolio_count', 'created_at']
    list_filter = ['institute', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'institute__name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['activate_managers', 'deactivate_managers']

    def portfolio_count(self, obj):
        return obj.portfolio_set.count()
    portfolio_count.short_description = 'Portfolios'

    def activate_managers(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} fund managers activated.")
    activate_managers.short_description = "Activate selected managers"

    def deactivate_managers(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} fund managers deactivated.")
    deactivate_managers.short_description = "Deactivate selected managers"


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['name', 'fund_manager', 'stock_count', 'created_at', 'updated_at']
    list_filter = ['fund_manager__institute', 'created_at', 'updated_at']
    search_fields = ['name', 'description', 'fund_manager__user__username']
    list_per_page = 25
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

    def stock_count(self, obj):
        return obj.stocks.count()
    stock_count.short_description = 'Stocks'


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'portfolio', 'quantity', 'price', 'total_value']
    list_filter = ['portfolio__fund_manager__institute', 'portfolio']
    search_fields = ['symbol', 'name', 'portfolio__name']
    list_per_page = 50

    def total_value(self, obj):
        if obj.price and obj.quantity:
            return f"${obj.price * obj.quantity:,.2f}"
        return "-"
    total_value.short_description = 'Total Value'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_email', 'institute', 'get_role', 'is_active', 'last_login', 'created_at']
    list_filter = ['institute', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'institute__name']
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['activate_profiles', 'deactivate_profiles']

    def get_role(self, obj):
        return obj.get_role()
    get_role.short_description = 'Role'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def last_login(self, obj):
        return obj.user.last_login
    last_login.short_description = 'Last Login'

    def activate_profiles(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} user profiles activated.")
    activate_profiles.short_description = "Activate selected profiles"

    def deactivate_profiles(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} user profiles deactivated.")
    deactivate_profiles.short_description = "Deactivate selected profiles"


@admin.register(InstituteSettings)
class InstituteSettingsAdmin(admin.ModelAdmin):
    list_display = ['institute', 'allow_analytics', 'allow_risk_analysis', 'allow_ai_features', 'max_portfolios_per_manager']
    list_filter = ['allow_analytics', 'allow_risk_analysis', 'allow_ai_features']
    search_fields = ['institute__name']
    list_per_page = 25


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'institute', 'role', 'status', 'invited_by', 'created_at', 'expires_at']
    list_filter = ['status', 'role', 'institute', 'created_at']
    search_fields = ['email', 'institute__name', 'invited_by__username']
    readonly_fields = ['token', 'created_at']
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['resend_invitations', 'cancel_invitations']

    def resend_invitations(self, request, queryset):
        # Add logic to resend invitations
        self.message_user(request, f"{queryset.count()} invitations will be resent (functionality to be implemented).")
    resend_invitations.short_description = "Resend selected invitations"

    def cancel_invitations(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"{queryset.count()} invitations cancelled.")
    cancel_invitations.short_description = "Cancel selected invitations"


@admin.register(HistoricalStockData)
class HistoricalStockDataAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'portfolio', 'date', 'adjusted_close']
    list_filter = ['portfolio', 'date', 'symbol']
    search_fields = ['symbol', 'portfolio__name']
    list_per_page = 50
    date_hierarchy = 'date'
    readonly_fields = ['date']
