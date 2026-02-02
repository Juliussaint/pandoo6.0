from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core
    path('', core_views.dashboard, name='dashboard'),
    
    # Apps
    path('products/', include('products.urls')),
    path('stock/', include('stock.urls')),
    path('transactions/', include('transactions.urls')),
    path('purchases/', include('purchases.urls')),
    path('suppliers/', include('suppliers.urls')),
    
    # Auth
    path('accounts/login/', core_views.login_view, name='login'),
    path('accounts/logout/', core_views.logout_view, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]