from django.db import models
from django.contrib.auth.models import User
from django.db import transaction as db_transaction

class TransactionType(models.TextChoices):
    PURCHASE = 'PURCHASE', 'Purchase'
    SALE = 'SALE', 'Sale'
    ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
    RETURN_IN = 'RETURN_IN', 'Return In'
    RETURN_OUT = 'RETURN_OUT', 'Return Out'
    TRANSFER = 'TRANSFER', 'Transfer'
    DAMAGE = 'DAMAGE', 'Damage/Loss'


class Transaction(models.Model):
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='transactions')
    location = models.ForeignKey('stock.Location', on_delete=models.CASCADE, related_name='transactions')
    
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    reference_number = models.CharField(max_length=100, blank=True, help_text="PO number, invoice number, etc.")
    notes = models.TextField(blank=True)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inventory_transactions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['product', 'location']),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} ({self.quantity}) on {self.created_at}"

    def save(self, *args, **kwargs):
        from stock.models import Stock
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            with db_transaction.atomic():
                stock, created = Stock.objects.select_for_update().get_or_create(
                    product=self.product,
                    location=self.location,
                    defaults={'quantity': 0}
                )
                
                if self.transaction_type in ['PURCHASE', 'RETURN_IN']:
                    stock.quantity += self.quantity
                elif self.transaction_type in ['SALE', 'RETURN_OUT', 'DAMAGE']:
                    stock.quantity -= self.quantity
                elif self.transaction_type == 'ADJUSTMENT':
                    stock.quantity = self.quantity
                
                stock.save()


class StockTransfer(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_TRANSIT', 'In Transit'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    transfer_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    from_location = models.ForeignKey('stock.Location', on_delete=models.CASCADE, related_name='transfers_out')
    to_location = models.ForeignKey('stock.Location', on_delete=models.CASCADE, related_name='transfers_in')
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    notes = models.TextField(blank=True)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='initiated_transfers')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transfers')
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Transfer {self.transfer_number}: {self.product.name}"