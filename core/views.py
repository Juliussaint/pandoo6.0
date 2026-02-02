from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta

from products.models import Product
from stock.models import Stock, StockAlert, Location
from transactions.models import Transaction, TransactionType
from purchases.models import PurchaseOrder

@login_required
def dashboard(request):
    # Get date range for statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Product statistics
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(
        stocks__quantity__lte=F('reorder_point'),
        is_active=True
    ).distinct().count()
    out_of_stock = Product.objects.filter(
        stocks__quantity=0,
        is_active=True
    ).distinct().count()
    
    # Stock value
    total_stock_value = 0
    stocks = Stock.objects.select_related('product').all()
    for stock in stocks:
        total_stock_value += stock.quantity * stock.product.unit_cost
    
    # Recent transactions
    recent_transactions = Transaction.objects.select_related(
        'product', 'location', 'user'
    ).order_by('-created_at')[:10]
    
    # Transactions this week
    transactions_this_week = Transaction.objects.filter(
        created_at__gte=week_ago
    ).count()
    
    # Purchase orders statistics
    pending_pos = PurchaseOrder.objects.filter(
        status__in=['DRAFT', 'SENT', 'PARTIAL']
    ).count()
    
    # Active alerts
    active_alerts = StockAlert.objects.filter(
        is_resolved=False
    ).select_related('product').order_by('-created_at')[:5]
    
    # Top products by transaction volume (last 30 days)
    top_products = Transaction.objects.filter(
        created_at__gte=month_ago
    ).values('product__name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]
    
    # Transaction type breakdown (last 30 days)
    transaction_breakdown = Transaction.objects.filter(
        created_at__gte=month_ago
    ).values('transaction_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Locations with stock count
    locations_data = []
    for location in Location.objects.filter(is_active=True):
        stock_count = Stock.objects.filter(location=location).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        locations_data.append({
            'name': location.name,
            'stock_count': stock_count
        })
    
    # Recent purchase orders
    recent_pos = PurchaseOrder.objects.select_related(
        'supplier', 'location'
    ).order_by('-created_at')[:5]
    
    context = {
        # Summary stats
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'out_of_stock': out_of_stock,
        'total_stock_value': total_stock_value,
        'transactions_this_week': transactions_this_week,
        'pending_pos': pending_pos,
        
        # Lists
        'recent_transactions': recent_transactions,
        'active_alerts': active_alerts,
        'top_products': top_products,
        'transaction_breakdown': transaction_breakdown,
        'locations_data': locations_data,
        'recent_pos': recent_pos,
    }
    
    return render(request, 'core/dashboard.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')