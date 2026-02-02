from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.purchase_order_list, name='purchase_order_list'),
    path('<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('create/', views.purchase_order_create, name='purchase_order_create'),
    path('<int:pk>/update/', views.purchase_order_update, name='purchase_order_update'),
    path('<int:pk>/send/', views.purchase_order_send, name='purchase_order_send'),
    path('<int:pk>/cancel/', views.purchase_order_cancel, name='purchase_order_cancel'),
    path('<int:po_pk>/receive/', views.goods_receipt_create, name='goods_receipt_create'),
]