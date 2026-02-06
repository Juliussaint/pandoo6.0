from django.contrib import admin
from .models import Category, Product, ProductVariation

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'product_count', 'created_at']
    list_filter = ['created_at', 'parent']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'parent', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1
    fields = ['name', 'value', 'sku_suffix', 'price_adjustment']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'supplier', 'unit_cost', 'selling_price', 
                    'reorder_point', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'supplier', 'created_at']
    search_fields = ['sku', 'name', 'barcode', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    inlines = [ProductVariationInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('sku', 'name', 'description', 'category', 'supplier', 'image')
        }),
        ('Pricing', {
            'fields': ('unit_cost', 'selling_price')
        }),
        ('Inventory Settings', {
            'fields': ('reorder_point', 'reorder_quantity', 'barcode')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category', 'supplier')

@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'value', 'sku_suffix', 'price_adjustment']
    list_filter = ['product', 'name']
    search_fields = ['product__name', 'name', 'value']