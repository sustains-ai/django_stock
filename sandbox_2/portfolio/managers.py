# Tenant-Aware Model Managers for Multi-Tenant SaaS

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from .middleware import get_current_tenant


class TenantManager(models.Manager):
    """
    Manager that automatically filters querysets by the current tenant.
    This ensures complete data isolation between organizations.
    """
    
    def get_queryset(self):
        """
        Override get_queryset to filter by current tenant.
        """
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        
        if tenant:
            # Filter by organization field
            if hasattr(self.model, 'organization'):
                return queryset.filter(organization=tenant)
            else:
                # If model doesn't have organization field, return unfiltered
                return queryset
        else:
            # No tenant context - return empty queryset for security
            return queryset.none()

    def create(self, **kwargs):
        """
        Override create to automatically set organization field.
        """
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'organization'):
            kwargs['organization'] = tenant
        return super().create(**kwargs)

    def get_or_create(self, defaults=None, **kwargs):
        """
        Override get_or_create to automatically set organization field.
        """
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'organization'):
            kwargs['organization'] = tenant
            if defaults:
                defaults['organization'] = tenant
        return super().get_or_create(defaults=defaults, **kwargs)


class TenantAwareModel(models.Model):
    """
    Abstract base model that provides tenant awareness.
    All tenant-aware models should inherit from this.
    """
    
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        help_text="Organization this record belongs to"
    )
    
    objects = TenantManager()
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically set organization if not set.
        """
        if not self.organization_id:
            tenant = get_current_tenant()
            if tenant:
                self.organization = tenant
            else:
                raise ImproperlyConfigured(
                    "Cannot save model without tenant context. "
                    "Make sure TenantMiddleware is properly configured."
                )
        super().save(*args, **kwargs)


class OrganizationManager(models.Manager):
    """
    Manager for Organization model - no tenant filtering needed.
    """
    
    def get_queryset(self):
        return super().get_queryset()


class UserManager(models.Manager):
    """
    Manager for User model - no tenant filtering needed.
    """
    
    def get_queryset(self):
        return super().get_queryset()


class TenantContextManager:
    """
    Context manager to set tenant context for specific operations.
    """
    
    def __init__(self, tenant):
        self.tenant = tenant
        self.previous_tenant = None
    
    def __enter__(self):
        self.previous_tenant = get_current_tenant()
        set_current_tenant(self.tenant)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        set_current_tenant(self.previous_tenant)


def with_tenant(tenant):
    """
    Decorator to run a function with a specific tenant context.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with TenantContextManager(tenant):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def get_tenant_queryset(model_class, tenant=None):
    """
    Utility function to get a queryset filtered by tenant.
    """
    if tenant is None:
        tenant = get_current_tenant()
    
    if not tenant:
        return model_class.objects.none()
    
    if hasattr(model_class, 'organization'):
        return model_class.objects.filter(organization=tenant)
    else:
        return model_class.objects.all()


def create_tenant_aware_object(model_class, **kwargs):
    """
    Utility function to create an object with tenant context.
    """
    tenant = get_current_tenant()
    if tenant and hasattr(model_class, 'organization'):
        kwargs['organization'] = tenant
    
    return model_class.objects.create(**kwargs)
