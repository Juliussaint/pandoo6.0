from django.contrib import admin
from .models import Transaction, TransactionType, StockTransfer

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'transaction_type', 'product', 'location', 
                    'quantity', 'unit_price', 'user', 'reference_number']
    list_filter = ['transaction_type', 'created_at', 'location']
    search_fields = ['product__name', 'product__sku', 'reference_number', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_type', 'product', 'location', 'quantity', 'unit_price')
        }),
        ('Reference', {
            'fields': ('reference_number', 'notes')
        }),
        ('Metadata', {
            'fields': ('user', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('product', 'location', 'user')
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing transactions
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete transactions
        return request.user.is_superuser

@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ['transfer_number', 'product', 'from_location', 'to_location', 
                    'quantity', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['transfer_number', 'product__name', 'product__sku']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = (
        ('Transfer Information', {
            'fields': ('transfer_number', 'product', 'from_location', 'to_location', 'quantity')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('Users', {
            'fields': ('initiated_by', 'received_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
    )