from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone

class ActivityLogMiddleware(MiddlewareMixin):
    """
    Middleware to track user activity and auto-logout inactive users
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            # Update last activity
            now = timezone.now()
            request.session['last_activity'] = now.isoformat()
            
            # Auto-logout after 2 hours of inactivity (optional)
            # Uncomment below if you want auto-logout feature
            # last_activity = request.session.get('last_activity')
            # if last_activity:
            #     last_activity_time = datetime.fromisoformat(last_activity)
            #     if timezone.make_aware(last_activity_time) < now - timedelta(hours=2):
            #         logout(request)
            #         messages.warning(request, 'You have been logged out due to inactivity.')
            #         return redirect('login')
        
        return None