from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Stock(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='stocks')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='stocks')
    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0, help_text="Quantity reserved for orders")
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'location')
        ordering = ['product', 'location']

    def __str__(self):
        return f"{self.product.name} at {self.location.name}: {self.quantity}"

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity


class StockAlert(models.Model):
    ALERT_TYPES = [
        ('LOW_STOCK', 'Low Stock'),
        ('OUT_OF_STOCK', 'Out of Stock'),
        ('OVERSTOCK', 'Overstock'),
    ]
    
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='alerts')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.alert_type} - {self.product.name}"