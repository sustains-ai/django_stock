# SaaS Authentication Views for Multi-Tenant Portfolio Management

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
import uuid

from .models import Organization, OrganizationAdmin, FundManager, Client, Portfolio
from .forms_saas import (
    OrganizationRegistrationForm, 
    UserRegistrationForm, 
    OrganizationLoginForm,
    FundManagerRegistrationForm,
    ClientRegistrationForm,
    OrganizationSettingsForm,
    UserProfileForm
)


def saas_home(request):
    """Landing page for SaaS platform"""
    return render(request, 'portfolio/saas_home.html', {
        'organizations_count': Organization.objects.filter(is_active=True).count(),
        'total_users': OrganizationAdmin.objects.count() + FundManager.objects.count() + Client.objects.count()
    })


def organization_signup(request):
    """Organization registration and admin user creation"""
    if request.method == 'POST':
        org_form = OrganizationRegistrationForm(request.POST)
        user_form = UserRegistrationForm(request.POST)
        
        if org_form.is_valid() and user_form.is_valid():
            with transaction.atomic():
                # Create organization
                organization = org_form.save(commit=False)
                organization.subscription_status = 'trial'
                organization.trial_ends_at = timezone.now() + timezone.timedelta(days=14)
                organization.save()
                
                # Create user
                user = user_form.save(commit=False)
                user.is_active = True
                user.save()
                
                # Create organization admin
                admin = OrganizationAdmin.objects.create(
                    user=user,
                    organization=organization,
                    is_primary_admin=True,
                    can_manage_billing=True,
                    can_manage_users=True,
                    can_view_analytics=True
                )
                
                # Login the user
                login(request, user)
                
                messages.success(request, f'Welcome to {organization.name}! Your 14-day trial has started.')
                return redirect('saas_dashboard')
    else:
        org_form = OrganizationRegistrationForm()
        user_form = UserRegistrationForm()
    
    return render(request, 'portfolio/saas_organization_signup.html', {
        'org_form': org_form,
        'user_form': user_form
    })


def organization_login(request):
    """Organization-based login"""
    if request.method == 'POST':
        form = OrganizationLoginForm(request.POST)
        
        if form.is_valid():
            organization_slug = form.cleaned_data['organization_slug']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Authenticate user
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Check if user belongs to the organization
                organization = get_object_or_404(Organization, slug=organization_slug, is_active=True)
                
                # Check user's role in organization
                user_role = None
                if hasattr(user, 'organizationadmin') and user.organizationadmin.organization == organization:
                    user_role = 'admin'
                elif hasattr(user, 'fundmanager') and user.fundmanager.organization == organization:
                    user_role = 'fund_manager'
                elif hasattr(user, 'client') and user.client.organization == organization:
                    user_role = 'client'
                
                if user_role:
                    login(request, user)
                    request.session['organization_id'] = str(organization.id)
                    request.session['user_role'] = user_role
                    
                    messages.success(request, f'Welcome back to {organization.name}!')
                    return redirect('saas_dashboard')
                else:
                    messages.error(request, 'You are not authorized to access this organization.')
            else:
                messages.error(request, 'Invalid credentials.')
    else:
        form = OrganizationLoginForm()
    
    return render(request, 'portfolio/saas_organization_login.html', {
        'form': form
    })


@login_required
def saas_dashboard(request):
    """SaaS dashboard with role-based content"""
    user = request.user
    organization_id = request.session.get('organization_id')
    user_role = request.session.get('user_role')
    
    if not organization_id:
        messages.error(request, 'No organization selected.')
        return redirect('organization_login')
    
    organization = get_object_or_404(Organization, id=organization_id)
    
    # Get user's role object
    role_object = None
    if user_role == 'admin':
        role_object = getattr(user, 'organizationadmin', None)
    elif user_role == 'fund_manager':
        role_object = getattr(user, 'fundmanager', None)
    elif user_role == 'client':
        role_object = getattr(user, 'client', None)
    
    # Dashboard data based on role
    dashboard_data = {
        'organization': organization,
        'user_role': user_role,
        'role_object': role_object,
        'usage_stats': organization.get_usage_stats(),
        'is_trial': organization.is_trial,
        'trial_ends_at': organization.trial_ends_at,
    }
    
    # Add role-specific data
    if user_role == 'admin':
        dashboard_data.update({
            'fund_managers': FundManager.objects.filter(organization=organization),
            'clients': Client.objects.filter(organization=organization),
            'total_portfolios': Portfolio.objects.filter(organization=organization).count(),
        })
    elif user_role == 'fund_manager':
        dashboard_data.update({
            'my_clients': Client.objects.filter(fund_manager=role_object),
            'my_portfolios': Portfolio.objects.filter(fund_manager=role_object),
        })
    elif user_role == 'client':
        dashboard_data.update({
            'my_portfolios': Portfolio.objects.filter(client=role_object),
            'fund_manager': role_object.fund_manager,
        })
    
    return render(request, 'portfolio/saas_dashboard.html', dashboard_data)


@login_required
def add_fund_manager(request):
    """Add a new fund manager to the organization"""
    organization_id = request.session.get('organization_id')
    user_role = request.session.get('user_role')
    
    if user_role != 'admin':
        messages.error(request, 'Only organization admins can add fund managers.')
        return redirect('saas_dashboard')
    
    organization = get_object_or_404(Organization, id=organization_id)
    
    if not organization.can_add_fund_manager():
        messages.error(request, 'You have reached the maximum number of fund managers for your plan.')
        return redirect('saas_dashboard')
    
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        fm_form = FundManagerRegistrationForm(request.POST)
        
        if user_form.is_valid() and fm_form.is_valid():
            with transaction.atomic():
                # Create user
                user = user_form.save(commit=False)
                user.is_active = True
                user.save()
                
                # Create fund manager
                fund_manager = fm_form.save(commit=False)
                fund_manager.user = user
                fund_manager.organization = organization
                fund_manager.save()
                
                messages.success(request, f'Fund manager {user.get_full_name()} has been added.')
                return redirect('saas_dashboard')
    else:
        user_form = UserRegistrationForm()
        fm_form = FundManagerRegistrationForm()
    
    return render(request, 'portfolio/saas_add_fund_manager.html', {
        'user_form': user_form,
        'fm_form': fm_form,
        'organization': organization
    })


@login_required
def add_client(request):
    """Add a new client to the organization"""
    organization_id = request.session.get('organization_id')
    user_role = request.session.get('user_role')
    
    if user_role not in ['admin', 'fund_manager']:
        messages.error(request, 'You are not authorized to add clients.')
        return redirect('saas_dashboard')
    
    organization = get_object_or_404(Organization, id=organization_id)
    
    if not organization.can_add_client():
        messages.error(request, 'You have reached the maximum number of clients for your plan.')
        return redirect('saas_dashboard')
    
    # Get fund managers for assignment
    fund_managers = FundManager.objects.filter(organization=organization, is_active=True)
    
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        client_form = ClientRegistrationForm(request.POST)
        
        if user_form.is_valid() and client_form.is_valid():
            with transaction.atomic():
                # Create user
                user = user_form.save(commit=False)
                user.is_active = True
                user.save()
                
                # Create client
                client = client_form.save(commit=False)
                client.user = user
                client.organization = organization
                
                # Assign to fund manager
                if user_role == 'fund_manager':
                    # Get current user's fund manager object
                    current_fm = getattr(request.user, 'fundmanager', None)
                    client.fund_manager = current_fm
                else:
                    # Admin can assign to any fund manager
                    fund_manager_id = request.POST.get('fund_manager')
                    if fund_manager_id:
                        client.fund_manager = get_object_or_404(FundManager, id=fund_manager_id)
                    else:
                        messages.error(request, 'Please select a fund manager.')
                        return render(request, 'portfolio/saas_add_client.html', {
                            'user_form': user_form,
                            'client_form': client_form,
                            'organization': organization,
                            'fund_managers': fund_managers
                        })
                
                client.save()
                
                messages.success(request, f'Client {user.get_full_name()} has been added.')
                return redirect('saas_dashboard')
    else:
        user_form = UserRegistrationForm()
        client_form = ClientRegistrationForm()
    
    return render(request, 'portfolio/saas_add_client.html', {
        'user_form': user_form,
        'client_form': client_form,
        'organization': organization,
        'fund_managers': fund_managers
    })


@login_required
def organization_settings(request):
    """Organization settings management"""
    organization_id = request.session.get('organization_id')
    user_role = request.session.get('user_role')
    
    if user_role != 'admin':
        messages.error(request, 'Only organization admins can manage settings.')
        return redirect('saas_dashboard')
    
    organization = get_object_or_404(Organization, id=organization_id)
    
    if request.method == 'POST':
        form = OrganizationSettingsForm(request.POST, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, 'Organization settings updated successfully.')
            return redirect('organization_settings')
    else:
        form = OrganizationSettingsForm(instance=organization)
    
    return render(request, 'portfolio/saas_organization_settings.html', {
        'form': form,
        'organization': organization
    })


@login_required
def user_profile(request):
    """User profile management"""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=user)
    
    return render(request, 'portfolio/saas_user_profile.html', {
        'form': form,
        'user': user
    })


def saas_logout(request):
    """SaaS logout with session cleanup"""
    logout(request)
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('saas_home')


@login_required
def switch_organization(request):
    """Switch between organizations (for users with multiple roles)"""
    user = request.user
    organizations = []
    
    # Get all organizations user belongs to
    if hasattr(user, 'organizationadmin'):
        organizations.append({
            'id': str(user.organizationadmin.organization.id),
            'name': user.organizationadmin.organization.name,
            'role': 'admin'
        })
    
    if hasattr(user, 'fundmanager'):
        organizations.append({
            'id': str(user.fundmanager.organization.id),
            'name': user.fundmanager.organization.name,
            'role': 'fund_manager'
        })
    
    if hasattr(user, 'client'):
        organizations.append({
            'id': str(user.client.organization.id),
            'name': user.client.organization.name,
            'role': 'client'
        })
    
    if request.method == 'POST':
        org_id = request.POST.get('organization_id')
        if org_id:
            request.session['organization_id'] = org_id
            # Find the role for this organization
            for org in organizations:
                if org['id'] == org_id:
                    request.session['user_role'] = org['role']
                    break
            messages.success(request, 'Organization switched successfully.')
            return redirect('saas_dashboard')
    
    return render(request, 'portfolio/saas_switch_organization.html', {
        'organizations': organizations
    })
