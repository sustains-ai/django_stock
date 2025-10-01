# Consolidated Middleware for Multi-Tenant SaaS Application

from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from .models import Organization


class TenantMiddleware:
    """
    Middleware to handle multi-tenancy by resolving tenant from subdomain or URL.
    This middleware extracts the tenant information and makes it available to views.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract tenant from subdomain or URL
        request.tenant = self.get_tenant(request)
        
        # Add tenant to request context for templates
        if hasattr(request, 'tenant') and request.tenant:
            request.tenant_context = {
                'tenant': request.tenant,
                'tenant_name': request.tenant.name,
                'tenant_slug': request.tenant.slug,
            }
        else:
            request.tenant_context = None
            
        response = self.get_response(request)
        return response

    def get_tenant(self, request):
        """
        Extract tenant from subdomain or URL path.
        Supports both subdomain-based and path-based tenancy.
        """
        host = request.get_host().split(':')[0]
        
        # Remove 'www.' prefix if present
        if host.startswith('www.'):
            host = host[4:]
        
        # Check if it's a tenant subdomain (e.g., acme.yourdomain.com)
        if '.' in host and not host.endswith('.yourdomain.com'):
            tenant_slug = host.split('.')[0]
            try:
                return Organization.objects.get(
                    slug=tenant_slug, 
                    is_active=True
                )
            except:
                # Tenant not found - could redirect to main site or show 404
                return None
        
        # Check for tenant in URL path (e.g., /acme/dashboard/)
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) > 0:
            potential_tenant_slug = path_parts[0]
            try:
                return Organization.objects.get(
                    slug=potential_tenant_slug,
                    is_active=True
                )
            except:
                pass
        
        # No tenant found
        return None


class TenantRequiredMiddleware:
    """
    Middleware to ensure tenant is present for tenant-specific views.
    Redirects to tenant selection if no tenant is found.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip tenant check for certain paths
        skip_paths = [
            '/admin/',
            '/accounts/',
            '/api/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return self.get_response(request)
        
        # Check if tenant is required for this view
        if self.requires_tenant(request):
            if not hasattr(request, 'tenant') or not request.tenant:
                # No tenant found - redirect to tenant selection
                return redirect('tenant_selection')
        
        response = self.get_response(request)
        return response

    def requires_tenant(self, request):
        """
        Determine if the current view requires a tenant.
        """
        # Views that require tenant
        tenant_required_paths = [
            '/dashboard/',
            '/portfolios/',
            '/analytics/',
            '/risk/',
            '/settings/',
        ]
        
        return any(request.path.startswith(path) for path in tenant_required_paths)


class SaaSContextMiddleware(MiddlewareMixin):
    """
    Middleware to manage SaaS context including organization and user roles.
    This ensures proper multi-tenant isolation and role-based access.
    """
    
    def process_request(self, request):
        """Process request to set SaaS context"""
        # Skip middleware for certain paths
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/saas-home/',
            '/organization-signup/',
            '/organization-login/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return None
        
        # Get organization context
        organization_id = request.session.get('organization_id')
        user_role = request.session.get('user_role')
        
        if not organization_id or not user_role:
            # User needs to select organization
            if request.path not in ['/switch-organization/', '/logout/']:
                return HttpResponseRedirect(reverse('switch_organization'))
            return None
        
        # Validate organization exists and is active
        try:
            organization = Organization.objects.get(id=organization_id, is_active=True)
            request.organization = organization
        except Organization.DoesNotExist:
            # Organization no longer exists or is inactive
            request.session.pop('organization_id', None)
            request.session.pop('user_role', None)
            messages.error(request, 'Your organization is no longer active.')
            return HttpResponseRedirect(reverse('organization_login'))
        
        # Validate user role in organization
        user = request.user
        is_valid_role = False
        
        if user_role == 'admin':
            is_valid_role = (
                hasattr(user, 'organizationadmin') and 
                user.organizationadmin.organization == organization
            )
        elif user_role == 'fund_manager':
            is_valid_role = (
                hasattr(user, 'fundmanager') and 
                user.fundmanager.organization == organization
            )
        elif user_role == 'client':
            is_valid_role = (
                hasattr(user, 'client') and 
                user.client.organization == organization
            )
        
        if not is_valid_role:
            # User role is invalid for this organization
            request.session.pop('organization_id', None)
            request.session.pop('user_role', None)
            messages.error(request, 'You are not authorized to access this organization.')
            return HttpResponseRedirect(reverse('organization_login'))
        
        # Set role object for easy access
        if user_role == 'admin':
            request.role_object = getattr(user, 'organizationadmin', None)
        elif user_role == 'fund_manager':
            request.role_object = getattr(user, 'fundmanager', None)
        elif user_role == 'client':
            request.role_object = getattr(user, 'client', None)
        
        return None


class OrganizationAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce organization-based access control.
    Ensures users can only access data from their organization.
    """
    
    def process_request(self, request):
        """Process request to enforce organization access"""
        # Skip for certain paths
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/saas-home/',
            '/organization-signup/',
            '/organization-login/',
            '/switch-organization/',
            '/logout/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Only apply to authenticated users with organization context
        if not (request.user.is_authenticated and hasattr(request, 'organization')):
            return None
        
        # Add organization filter to request for use in views
        request.organization_filter = {'organization': request.organization}
        
        return None


class SubscriptionMiddleware(MiddlewareMixin):
    """
    Middleware to check subscription status and enforce limits.
    """
    
    def process_request(self, request):
        """Process request to check subscription status"""
        # Skip for certain paths
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/saas-home/',
            '/organization-signup/',
            '/organization-login/',
            '/switch-organization/',
            '/logout/',
            '/organization-settings/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Only apply to authenticated users with organization context
        if not (request.user.is_authenticated and hasattr(request, 'organization')):
            return None
        
        organization = request.organization
        
        # Check if organization is active
        if not organization.is_active:
            messages.error(request, 'Your organization account has been suspended.')
            return HttpResponseRedirect(reverse('organization_login'))
        
        # Check subscription status
        if organization.subscription_status in ['past_due', 'canceled', 'suspended']:
            messages.error(request, 'Your subscription is not active. Please update your billing information.')
            return HttpResponseRedirect(reverse('organization_settings'))
        
        # Check trial expiration
        if organization.is_trial and organization.trial_ends_at:
            from django.utils import timezone
            if timezone.now() > organization.trial_ends_at:
                messages.error(request, 'Your trial has expired. Please upgrade your subscription.')
                return HttpResponseRedirect(reverse('organization_settings'))
        
        return None


class UsageLimitMiddleware(MiddlewareMixin):
    """
    Middleware to enforce usage limits based on subscription plan.
    """
    
    def process_request(self, request):
        """Process request to check usage limits"""
        # Skip for certain paths
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/saas-home/',
            '/organization-signup/',
            '/organization-login/',
            '/switch-organization/',
            '/logout/',
            '/organization-settings/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Only apply to authenticated users with organization context
        if not (request.user.is_authenticated and hasattr(request, 'organization')):
            return None
        
        organization = request.organization
        
        # Check usage limits for specific actions
        if request.path in ['/add-fund-manager/', '/add-client/', '/add-portfolio/']:
            if request.method == 'POST':
                if request.path == '/add-fund-manager/' and not organization.can_add_fund_manager():
                    messages.error(request, 'You have reached the maximum number of fund managers for your plan.')
                    return HttpResponseRedirect(reverse('saas_dashboard'))
                
                elif request.path == '/add-client/' and not organization.can_add_client():
                    messages.error(request, 'You have reached the maximum number of clients for your plan.')
                    return HttpResponseRedirect(reverse('saas_dashboard'))
                
                elif request.path == '/add-portfolio/' and not organization.can_add_portfolio():
                    messages.error(request, 'You have reached the maximum number of portfolios for your plan.')
                    return HttpResponseRedirect(reverse('saas_dashboard'))
        
        return None


class TenantContextMiddleware:
    """
    Middleware to add tenant context to all requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        """
        Add tenant context to template responses.
        """
        if hasattr(response, 'context_data') and response.context_data:
            if hasattr(request, 'tenant_context') and request.tenant_context:
                response.context_data.update(request.tenant_context)
        return response


def get_current_tenant():
    """
    Utility function to get the current tenant from thread-local storage.
    This can be used in models and other parts of the application.
    """
    import threading
    thread_local = threading.local()
    return getattr(thread_local, 'tenant', None)


def set_current_tenant(tenant):
    """
    Utility function to set the current tenant in thread-local storage.
    """
    import threading
    thread_local = threading.local()
    thread_local.tenant = tenant
