# 🏢 Multi-Company Role-Based Dashboard Implementation Plan

## 📋 **Current State Analysis**

### **Existing Models:**
- ✅ `Institute` - Company/Organization model
- ✅ `InstituteRole` - Role assignments (admin, manager, analyst)
- ✅ `FundManager` - User profile with institute association
- ✅ `Portfolio` - Investment portfolios
- ✅ `Stock` - Individual stock holdings

### **Current Dashboard:**
- ✅ Single `modern_dashboard` view for Fund Managers only
- ✅ Basic portfolio metrics and KPIs
- ✅ Clean, modern UI with Bootstrap styling

---

## 🎯 **Implementation Goals**

### **1. Role-Based Dashboard Views**
- **Institute Admin Dashboard**: Company-wide analytics, user management, settings
- **Fund Manager Dashboard**: Current dashboard (portfolio management)
- **Analyst Dashboard**: Read-only analytics and reporting

### **2. Custom Admin System**
- Replace Django admin with custom admin interface
- Company management, user roles, system settings
- Password management for all users

### **3. Multi-Company Onboarding**
- Company registration and setup
- User invitation system
- Company-specific branding and settings

---

## 🏗️ **Detailed Implementation Plan**

### **Phase 1: Enhanced Models & Permissions**

#### **1.1 Update Institute Model**
```python
class Institute(models.Model):
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, unique=True)  # company.com
    logo = models.ImageField(upload_to='institutes/logos/', blank=True)
    primary_color = models.CharField(max_length=7, default='#007bff')  # Brand color
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    subscription_plan = models.CharField(max_length=50, default='basic')
    max_users = models.IntegerField(default=10)
    
    def __str__(self):
        return self.name
```

#### **1.2 Enhanced User Profile**
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    is_active = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### **1.3 Company Settings**
```python
class InstituteSettings(models.Model):
    institute = models.OneToOneField(Institute, on_delete=models.CASCADE)
    allow_analytics = models.BooleanField(default=True)
    allow_risk_analysis = models.BooleanField(default=True)
    allow_ai_features = models.BooleanField(default=True)
    max_portfolios_per_manager = models.IntegerField(default=50)
    data_retention_days = models.IntegerField(default=365)
```

### **Phase 2: Role-Based Dashboard Views**

#### **2.1 Dashboard Router**
```python
@login_required
def dashboard_router(request):
    """Route users to appropriate dashboard based on role"""
    user_profile = request.user.userprofile
    role = get_user_role(request.user, user_profile.institute)
    
    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'manager':
        return redirect('manager_dashboard')
    elif role == 'analyst':
        return redirect('analyst_dashboard')
    else:
        return redirect('login')
```

#### **2.2 Institute Admin Dashboard**
```python
@login_required
@admin_required
def admin_dashboard(request):
    """Company-wide dashboard for institute admins"""
    institute = request.user.userprofile.institute
    
    # Company metrics
    total_users = UserProfile.objects.filter(institute=institute).count()
    active_managers = FundManager.objects.filter(institute=institute, is_active=True).count()
    total_portfolios = Portfolio.objects.filter(fund_manager__institute=institute).count()
    total_value = calculate_institute_total_value(institute)
    
    # Recent activity
    recent_portfolios = Portfolio.objects.filter(
        fund_manager__institute=institute
    ).order_by('-created_at')[:5]
    
    # User management
    pending_invitations = UserInvitation.objects.filter(
        institute=institute, 
        status='pending'
    )
    
    context = {
        'institute': institute,
        'total_users': total_users,
        'active_managers': active_managers,
        'total_portfolios': total_portfolios,
        'total_value': total_value,
        'recent_portfolios': recent_portfolios,
        'pending_invitations': pending_invitations,
    }
    
    return render(request, 'portfolio/admin_dashboard.html', context)
```

#### **2.3 Fund Manager Dashboard (Enhanced)**
```python
@login_required
@fund_manager_required
def manager_dashboard(request):
    """Enhanced dashboard for fund managers"""
    fund_manager = request.user.fundmanager
    portfolios = Portfolio.objects.filter(fund_manager=fund_manager)
    
    # Enhanced metrics
    portfolio_metrics = calculate_portfolio_metrics(portfolios)
    risk_summary = calculate_risk_summary(portfolios)
    performance_trends = get_performance_trends(portfolios)
    
    context = {
        'portfolios': portfolios,
        'metrics': portfolio_metrics,
        'risk_summary': risk_summary,
        'performance_trends': performance_trends,
    }
    
    return render(request, 'portfolio/manager_dashboard.html', context)
```

#### **2.4 Analyst Dashboard**
```python
@login_required
@analyst_required
def analyst_dashboard(request):
    """Read-only dashboard for analysts"""
    institute = request.user.userprofile.institute
    
    # Institute-wide analytics
    all_portfolios = Portfolio.objects.filter(
        fund_manager__institute=institute
    )
    
    # Analytics data
    performance_analytics = get_performance_analytics(all_portfolios)
    risk_analytics = get_risk_analytics(all_portfolios)
    market_insights = get_market_insights()
    
    context = {
        'institute': institute,
        'performance_analytics': performance_analytics,
        'risk_analytics': risk_analytics,
        'market_insights': market_insights,
    }
    
    return render(request, 'portfolio/analyst_dashboard.html', context)
```

### **Phase 3: Custom Admin System**

#### **3.1 Admin Views Structure**
```
/admin/
├── dashboard/          # Admin dashboard
├── users/             # User management
│   ├── list/          # All users
│   ├── create/         # Invite users
│   ├── edit/<id>/      # Edit user
│   └── roles/           # Role management
├── company/           # Company settings
│   ├── profile/        # Company profile
│   ├── branding/       # Logo, colors
│   └── settings/       # Company settings
├── analytics/         # Company analytics
└── reports/           # Generate reports
```

#### **3.2 User Management System**
```python
class UserInvitation(models.Model):
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

@login_required
@admin_required
def invite_user(request):
    """Invite new user to company"""
    if request.method == 'POST':
        form = UserInvitationForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.institute = request.user.userprofile.institute
            invitation.invited_by = request.user
            invitation.token = generate_invitation_token()
            invitation.save()
            
            # Send invitation email
            send_invitation_email(invitation)
            
            messages.success(request, f'Invitation sent to {invitation.email}')
            return redirect('admin_users')
    else:
        form = UserInvitationForm()
    
    return render(request, 'admin/invite_user.html', {'form': form})
```

#### **3.3 Password Management**
```python
@login_required
def change_password(request):
    """Allow users to change their password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password changed successfully')
            return redirect('dashboard')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'auth/change_password.html', {'form': form})

@login_required
@admin_required
def reset_user_password(request, user_id):
    """Admin can reset user passwords"""
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        new_password = generate_random_password()
        user.set_password(new_password)
        user.save()
        
        # Send new password via email
        send_password_reset_email(user, new_password)
        
        messages.success(request, f'Password reset for {user.username}')
        return redirect('admin_users')
    
    return render(request, 'admin/reset_password.html', {'user': user})
```

### **Phase 4: Multi-Company Onboarding**

#### **4.1 Company Registration**
```python
class CompanyRegistrationForm(forms.Form):
    company_name = forms.CharField(max_length=255)
    domain = forms.CharField(max_length=255, help_text="yourcompany.com")
    admin_email = forms.EmailField()
    admin_first_name = forms.CharField(max_length=100)
    admin_last_name = forms.CharField(max_length=100)
    admin_password = forms.CharField(widget=forms.PasswordInput())
    subscription_plan = forms.ChoiceField(choices=SUBSCRIPTION_PLANS)

def register_company(request):
    """Register new company and create admin user"""
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            # Create institute
            institute = Institute.objects.create(
                name=form.cleaned_data['company_name'],
                domain=form.cleaned_data['domain'],
                subscription_plan=form.cleaned_data['subscription_plan']
            )
            
            # Create admin user
            admin_user = User.objects.create_user(
                username=form.cleaned_data['admin_email'],
                email=form.cleaned_data['admin_email'],
                password=form.cleaned_data['admin_password'],
                first_name=form.cleaned_data['admin_first_name'],
                last_name=form.cleaned_data['admin_last_name']
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=admin_user,
                institute=institute
            )
            
            # Assign admin role
            InstituteRole.objects.create(
                user=admin_user,
                institute=institute,
                role='admin'
            )
            
            # Create fund manager profile
            FundManager.objects.create(
                user=admin_user,
                institute=institute
            )
            
            messages.success(request, 'Company registered successfully!')
            return redirect('login')
    else:
        form = CompanyRegistrationForm()
    
    return render(request, 'auth/register_company.html', {'form': form})
```

#### **4.2 Company Branding**
```python
@login_required
@admin_required
def company_branding(request):
    """Manage company branding"""
    institute = request.user.userprofile.institute
    
    if request.method == 'POST':
        form = CompanyBrandingForm(request.POST, request.FILES, instance=institute)
        if form.is_valid():
            form.save()
            messages.success(request, 'Branding updated successfully')
            return redirect('admin_branding')
    else:
        form = CompanyBrandingForm(instance=institute)
    
    return render(request, 'admin/branding.html', {'form': form})
```

### **Phase 5: Template Structure**

#### **5.1 Dashboard Templates**
```
templates/portfolio/
├── dashboards/
│   ├── admin_dashboard.html      # Institute admin dashboard
│   ├── manager_dashboard.html    # Fund manager dashboard
│   └── analyst_dashboard.html    # Analyst dashboard
├── admin/
│   ├── users/
│   │   ├── list.html
│   │   ├── invite.html
│   │   └── edit.html
│   ├── company/
│   │   ├── profile.html
│   │   ├── branding.html
│   │   └── settings.html
│   └── analytics/
│       └── company_analytics.html
└── auth/
    ├── register_company.html
    ├── accept_invitation.html
    └── change_password.html
```

#### **5.2 Dynamic Branding**
```html
<!-- In base.html -->
<style>
:root {
    --primary-color: {{ user.userprofile.institute.primary_color|default:'#007bff' }};
    --company-logo: url('{{ user.userprofile.institute.logo.url|default:'' }}');
}
</style>
```

### **Phase 6: URL Structure**

#### **6.1 URL Patterns**
```python
urlpatterns = [
    # Dashboard routing
    path('dashboard/', views.dashboard_router, name='dashboard'),
    
    # Role-specific dashboards
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('analyst/dashboard/', views.analyst_dashboard, name='analyst_dashboard'),
    
    # Admin management
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/invite/', views.invite_user, name='invite_user'),
    path('admin/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('admin/company/', views.company_settings, name='company_settings'),
    path('admin/branding/', views.company_branding, name='company_branding'),
    
    # Authentication
    path('register/company/', views.register_company, name='register_company'),
    path('invite/accept/<str:token>/', views.accept_invitation, name='accept_invitation'),
    path('change-password/', views.change_password, name='change_password'),
]
```

---

## 🚀 **Implementation Timeline**

### **Week 1: Foundation**
- [ ] Update models (Institute, UserProfile, InstituteSettings)
- [ ] Create migration files
- [ ] Update permissions system
- [ ] Create dashboard router

### **Week 2: Role-Based Dashboards**
- [ ] Implement admin dashboard
- [ ] Enhance manager dashboard
- [ ] Create analyst dashboard
- [ ] Update templates with role-based content

### **Week 3: Custom Admin System**
- [ ] User management interface
- [ ] Company settings management
- [ ] Password management system
- [ ] User invitation system

### **Week 4: Multi-Company Features**
- [ ] Company registration flow
- [ ] Branding customization
- [ ] Company-specific settings
- [ ] Testing and refinement

---

## 🔧 **Technical Considerations**

### **Database Changes**
- New models require migrations
- Existing data needs to be preserved
- Consider data migration scripts for existing users

### **Security**
- Role-based access control
- Company data isolation
- Secure invitation system
- Password policy enforcement

### **Performance**
- Efficient queries for dashboard metrics
- Caching for company-wide analytics
- Pagination for large user lists

### **User Experience**
- Intuitive role-based navigation
- Clear permission boundaries
- Responsive design for all dashboards
- Company branding consistency

---

## 📊 **Success Metrics**

### **Functional Requirements**
- ✅ Users see appropriate dashboard based on role
- ✅ Admins can manage users and company settings
- ✅ Multi-company isolation works correctly
- ✅ Password management functions properly

### **User Experience**
- ✅ Intuitive navigation for each role
- ✅ Consistent branding across company
- ✅ Fast loading dashboards
- ✅ Clear permission boundaries

### **Business Value**
- ✅ Scalable multi-company architecture
- ✅ Customizable company branding
- ✅ Comprehensive user management
- ✅ Role-based feature access

---

This implementation plan provides a comprehensive roadmap for building a sophisticated multi-company, role-based dashboard system that will scale with your business needs while maintaining security and user experience standards.
