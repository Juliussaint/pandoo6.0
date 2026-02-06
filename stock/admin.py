from django.contrib import admin
from .models import Location, Stock, StockAlert

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'stock_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'address']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Location Information', {
            'fields': ('name', 'code', 'address', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_count(self, obj):
        return obj.stocks.count()
    stock_count.short_description = 'Stock Items'

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'location', 'quantity', 'reserved_quantity', 
                    'available_quantity', 'last_updated']
    list_filter = ['location', 'last_updated']
    search_fields = ['product__name', 'product__sku', 'location__name']
    readonly_fields = ['last_updated']
    
    fieldsets = (
        ('Stock Information', {
            'fields': ('product', 'location')
        }),
        ('Quantities', {
            'fields': ('quantity', 'reserved_quantity')
        }),
        ('Metadata', {
            'fields': ('last_updated',)
        }),
    )
    
    def available_quantity(self, obj):
        return obj.available_quantity
    available_quantity.short_description = 'Available'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('product', 'location')

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'location', 'alert_type', 'is_resolved', 'created_at', 'resolved_at']
    list_filter = ['alert_type', 'is_resolved', 'created_at']
    search_fields = ['product__name', 'product__sku', 'location__name']
    readonly_fields = ['created_at', 'resolved_at']
    list_editable = ['is_resolved']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('product', 'location', 'alert_type')
        }),
        ('Status', {
            'fields': ('is_resolved', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('product', 'location')