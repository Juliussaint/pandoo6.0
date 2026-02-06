from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from core.decorators import permission_required
from core.models import UserProfile, AuditLog, UserRole
from core.decorators import log_activity
from .forms import UserForm, UserProfileForm

@login_required
@permission_required('can_manage_users')
def user_list(request):
    users = User.objects.select_related('profile').all()
    
    # Search
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Filter by role
    role = request.GET.get('role')
    if role:
        users = users.filter(profile__role=role)
    
    # Filter by active status
    is_active = request.GET.get('is_active')
    if is_active:
        users = users.filter(is_active=is_active == 'true')
    
    context = {
        'users': users,
        'search': search,
        'roles': UserRole.choices,
    }
    
    return render(request, 'users/user_list.html', context)

@login_required
@permission_required('can_manage_users')
def user_detail(request, pk):
    user = get_object_or_404(User.objects.select_related('profile'), pk=pk)
    
    # Get user's recent activities
    recent_activities = AuditLog.objects.filter(user=user).order_by('-timestamp')[:20]
    
    # Get statistics
    from transactions.models import Transaction
    from purchases.models import PurchaseOrder
    
    total_transactions = Transaction.objects.filter(user=user).count()
    total_purchase_orders = PurchaseOrder.objects.filter(created_by=user).count()
    
    context = {
        'user_obj': user,
        'recent_activities': recent_activities,
        'total_transactions': total_transactions,
        'total_purchase_orders': total_purchase_orders,
    }
    
    return render(request, 'users/user_detail.html', context)

@login_required
@permission_required('can_manage_users')
def user_create(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Save user
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            
            # UserProfile sudah otomatis dibuat oleh signal
            # Kita hanya perlu update field-fieldnya
            profile = user.profile  # 👈 AMBIL profile yang sudah dibuat oleh signal
            profile.role = profile_form.cleaned_data['role']
            profile.phone = profile_form.cleaned_data['phone']
            profile.department = profile_form.cleaned_data['department']
            profile.is_active = profile_form.cleaned_data['is_active']
            
            if profile_form.cleaned_data.get('avatar'):
                profile.avatar = profile_form.cleaned_data['avatar']
            
            profile.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='CREATE',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                description=f'Created new user: {user.username} with role {profile.get_role_display()}',
                request=request
            )
            
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('users:user_detail', pk=user.pk)
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Create User'
    }
    
    return render(request, 'users/user_form.html', context)

@login_required
@permission_required('can_manage_users')
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            
            # Only update password if provided
            password = user_form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            
            user.save()
            profile_form.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='UPDATE',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                description=f'Updated user: {user.username}',
                request=request
            )
            
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('users:user_detail', pk=user.pk)
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_obj': user,
        'title': 'Update User'
    }
    
    return render(request, 'users/user_form.html', context)

@login_required
@permission_required('can_manage_users')
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Prevent deleting self
    if user == request.user:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('users:user_list')
    
    if request.method == 'POST':
        username = user.username
        
        # Log activity before deleting
        log_activity(
            user=request.user,
            action='DELETE',
            model_name='User',
            object_id=user.id,
            object_repr=username,
            description=f'Deleted user: {username}',
            request=request
        )
        
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('users:user_list')
    
    context = {'user_obj': user}
    return render(request, 'users/user_confirm_delete.html', context)

@login_required
def user_profile(request):
    """View for users to edit their own profile"""
    user = request.user
    
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user.profile)
        
        # Remove role field - users cannot change their own role
        if 'role' in profile_form.fields:
            profile_form.fields['role'].disabled = True
        
        if profile_form.is_valid():
            profile_form.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='UPDATE',
                model_name='UserProfile',
                object_id=user.profile.id,
                object_repr=user.username,
                description=f'Updated own profile',
                request=request
            )
            
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('users:user_profile')
    else:
        profile_form = UserProfileForm(instance=user.profile)
        # Remove role field from form
        if 'role' in profile_form.fields:
            profile_form.fields['role'].disabled = True
    
    context = {
        'profile_form': profile_form,
        'user_obj': user,
    }
    
    return render(request, 'users/profile.html', context)

@login_required
@permission_required('can_view_activity_logs')
def activity_log(request):
    logs = AuditLog.objects.select_related('user').all()
    
    # Filter by user
    user_id = request.GET.get('user')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    # Filter by action
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)
    
    # Filter by model
    model_name = request.GET.get('model')
    if model_name:
        logs = logs.filter(model_name=model_name)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        logs = logs.filter(timestamp__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__lte=date_to)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    users = User.objects.filter(is_active=True).order_by('username')
    
    # Get unique model names from logs
    model_names = AuditLog.objects.values_list('model_name', flat=True).distinct().order_by('model_name')
    
    context = {
        'page_obj': page_obj,
        'users': users,
        'actions': AuditLog.ACTION_CHOICES,
        'model_names': model_names,
    }
    
    return render(request, 'users/activity_log.html', context)