from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('', views.stock_list, name='stock_list'),
    path('<int:pk>/', views.stock_detail, name='stock_detail'),
    path('<int:pk>/adjust/', views.stock_adjustment, name='stock_adjustment'),
    path('locations/', views.location_list, name='location_list'),
    path('locations/create/', views.location_create, name='location_create'),
    path('alerts/', views.stock_alerts, name='stock_alerts'),
    path('alerts/<int:pk>/resolve/', views.resolve_alert, name='resolve_alert'),

    # Bulk upload
    path('bulk-upload/', views.bulk_stock_upload, name='bulk_upload'),
    path('download-template/', views.download_stock_template, name='download_template'),
]