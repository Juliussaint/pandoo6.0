from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import AuditLog


def role_required(*roles):
    """
    Decorator untuk memastikan user memiliki role tertentu
    Usage: @role_required('ADMIN', 'MANAGER')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please log in to access this page.')
                return redirect('login')
            
            user_role = request.user.profile.role
            if user_role not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                
                # Log unauthorized access attempt
                log_activity(
                    user=request.user,
                    action='VIEW',
                    model_name='Permission Denied',
                    description=f'Attempted to access {request.path} without permission',
                    request=request
                )
                
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission_method):
    """
    Decorator untuk mengecek permission method dari UserProfile
    Usage: @permission_required('can_create_products')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please log in to access this page.')
                return redirect('login')
            
            has_permission = getattr(request.user.profile, permission_method, lambda: False)()
            if not has_permission:
                messages.error(request, 'You do not have permission to perform this action.')
                
                # Log unauthorized access attempt
                log_activity(
                    user=request.user,
                    action='VIEW',
                    model_name='Permission Denied',
                    description=f'Attempted to {permission_method} at {request.path}',
                    request=request
                )
                
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def log_activity(user, action, model_name, object_id=None, object_repr='', description='', request=None):
    """
    Helper function to log activity
    """
    ip_address = None
    user_agent = ''
    
    if request:
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent
    )