from django.contrib import admin
from .models import PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'received_quantity']
    readonly_fields = ['received_quantity']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'supplier', 'location', 'status', 'order_date', 
                    'expected_delivery', 'total_cost', 'created_by', 'created_at']
    list_filter = ['status', 'order_date', 'created_at', 'supplier']
    search_fields = ['po_number', 'supplier__name', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'actual_delivery']
    date_hierarchy = 'order_date'
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('Purchase Order Information', {
            'fields': ('po_number', 'supplier', 'location', 'status')
        }),
        ('Dates', {
            'fields': ('order_date', 'expected_delivery', 'actual_delivery')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('supplier', 'location', 'created_by')

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'product', 'quantity', 'unit_price', 
                    'total_cost', 'received_quantity', 'pending_quantity']
    list_filter = ['purchase_order__status', 'created_at']
    search_fields = ['purchase_order__po_number', 'product__name', 'product__sku']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Item Information', {
            'fields': ('purchase_order', 'product', 'quantity', 'unit_price')
        }),
        ('Receiving Status', {
            'fields': ('received_quantity',)
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

class GoodsReceiptItemInline(admin.TabularInline):
    model = GoodsReceiptItem
    extra = 0
    fields = ['po_item', 'quantity_received', 'notes']

@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'purchase_order', 'received_date', 
                    'received_by', 'created_at']
    list_filter = ['received_date', 'created_at']
    search_fields = ['receipt_number', 'purchase_order__po_number', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'received_date'
    inlines = [GoodsReceiptItemInline]
    
    fieldsets = (
        ('Receipt Information', {
            'fields': ('receipt_number', 'purchase_order', 'received_date')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('received_by', 'created_at')
        }),
    )

@admin.register(GoodsReceiptItem)
class GoodsReceiptItemAdmin(admin.ModelAdmin):
    list_display = ['goods_receipt', 'po_item', 'quantity_received']
    list_filter = ['goods_receipt__received_date']
    search_fields = ['goods_receipt__receipt_number', 'po_item__product__name']