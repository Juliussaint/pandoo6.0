import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# ============================================
# AUDIT LOG (UPGRADED)
# ============================================

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('VIEW', 'Viewed'),
        ('LOGIN', 'Logged In'),
        ('LOGOUT', 'Logged Out'),
        ('EXPORT', 'Exported'),
        ('IMPORT', 'Imported'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=100, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.IntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    changes = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        username = self.user.username if self.user else 'System'
        action_display = self.get_action_display() if hasattr(self, 'get_action_display') else self.action
        return f"{username} - {action_display} {self.model_name} at {self.timestamp}"


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
    
    def __str__(self):
        return self.key


# ============================================
# USER ROLES & PROFILES
# ============================================

class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrator'
    MANAGER = 'MANAGER', 'Manager'
    WAREHOUSE_STAFF = 'WAREHOUSE_STAFF', 'Warehouse Staff'
    VIEWER = 'VIEWER', 'Viewer'


def user_avatar_path(instance, filename):
    """
    Custom path untuk avatar: media/avatars/user_id/filename
    """
    ext = filename.split('.')[-1]
    filename = f"{instance.user.username}_{instance.user.id}.{ext}"
    return os.path.join('avatars', f'user_{instance.user.id}', filename)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.VIEWER)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to=user_avatar_path, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__username']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    # ============================================
    # PERMISSION HELPER METHODS
    # ============================================
    
    # Product Permissions
    def can_create_products(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_edit_products(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_delete_products(self):
        return self.role == UserRole.ADMIN
    
    def can_view_products(self):
        return True  # All roles can view
    
    # Purchase Order Permissions
    def can_create_purchase_orders(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_edit_purchase_orders(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_delete_purchase_orders(self):
        return self.role == UserRole.ADMIN
    
    def can_approve_purchase_orders(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_receive_goods(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.WAREHOUSE_STAFF]
    
    # Transaction Permissions
    def can_record_transactions(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.WAREHOUSE_STAFF]
    
    def can_view_transactions(self):
        return True
    
    # Stock Permissions
    def can_adjust_stock(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.WAREHOUSE_STAFF]
    
    def can_view_stock(self):
        return True
    
    # Supplier Permissions
    def can_create_suppliers(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_edit_suppliers(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_delete_suppliers(self):
        return self.role == UserRole.ADMIN
    
    def can_view_suppliers(self):
        return True
    
    # Location Permissions
    def can_manage_locations(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    # Report Permissions
    def can_view_reports(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_export_reports(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    # User Management Permissions
    def can_manage_users(self):
        return self.role == UserRole.ADMIN
    
    def can_view_activity_logs(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]


# ============================================
# SIGNALS
# ============================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile when a new User is created
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save UserProfile when User is saved
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()