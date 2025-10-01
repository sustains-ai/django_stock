# Role-Based Access Control for Portfolio Management

from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.contrib import messages
from functools import wraps
from .models import InstituteRole, FundManager, Portfolio


def get_user_institute_role(user, institute):
    """Get user's role in a specific institute"""
    try:
        role = InstituteRole.objects.get(user=user, institute=institute)
        return role.role
    except InstituteRole.DoesNotExist:
        return None


def get_user_institutes(user):
    """Get all institutes where user has a role"""
    return InstituteRole.objects.filter(user=user).select_related('institute')


def has_institute_admin_permission(user, institute):
    """Check if user is admin of the institute"""
    role = get_user_institute_role(user, institute)
    return role == 'admin'


def has_fund_manager_permission(user, institute):
    """Check if user is fund manager in the institute"""
    role = get_user_institute_role(user, institute)
    return role in ['admin', 'manager']


def has_analyst_permission(user, institute):
    """Check if user has analyst or higher access"""
    role = get_user_institute_role(user, institute)
    return role in ['admin', 'manager', 'analyst']


def institute_admin_required(view_func):
    """Decorator to require institute admin access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Get institute from kwargs or request
        institute_id = kwargs.get('institute_id')
        if not institute_id:
            messages.error(request, "Institute not specified")
            return redirect('dashboard')
        
        from .models import Institute
        try:
            institute = Institute.objects.get(id=institute_id)
        except Institute.DoesNotExist:
            messages.error(request, "Institute not found")
            return redirect('dashboard')
        
        if not has_institute_admin_permission(request.user, institute):
            messages.error(request, "Access denied. Institute admin access required.")
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def fund_manager_required(view_func):
    """Decorator to require fund manager access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user is a fund manager
        try:
            fund_manager = FundManager.objects.get(user=request.user)
            if not fund_manager.is_active:
                messages.error(request, "Your account is inactive")
                return redirect('login')
        except FundManager.DoesNotExist:
            messages.error(request, "Access denied. Fund manager account required.")
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def analyst_or_higher_required(view_func):
    """Decorator to require analyst or higher access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Get portfolio to determine institute
        portfolio_id = kwargs.get('portfolio_id')
        if portfolio_id:
            try:
                portfolio = Portfolio.objects.get(id=portfolio_id)
                institute = portfolio.fund_manager.institute
                
                if not has_analyst_permission(request.user, institute):
                    messages.error(request, "Access denied. Insufficient permissions.")
                    return redirect('dashboard')
            except Portfolio.DoesNotExist:
                messages.error(request, "Portfolio not found")
                return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def can_manage_portfolio(user, portfolio):
    """Check if user can manage a specific portfolio"""
    try:
        # User must be the fund manager of the portfolio
        if portfolio.fund_manager.user == user:
            return True
        
        # Or user must be admin of the portfolio's institute
        institute = portfolio.fund_manager.institute
        return has_institute_admin_permission(user, institute)
    except:
        return False


def can_view_portfolio(user, portfolio):
    """Check if user can view a specific portfolio"""
    try:
        # User can view if they can manage it
        if can_manage_portfolio(user, portfolio):
            return True
        
        # Or if they have analyst access to the institute
        institute = portfolio.fund_manager.institute
        return has_analyst_permission(user, institute)
    except:
        return False
