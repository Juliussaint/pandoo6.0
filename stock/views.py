from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.http import HttpResponse
from core.decorators import permission_required, log_activity
from .models import Stock, Location, StockAlert
from .forms import StockForm, LocationForm, StockAdjustmentForm
from products.models import Product

@login_required
def stock_list(request):
    stocks = Stock.objects.select_related('product', 'location').all()
    
    # Search
    search = request.GET.get('search', '')
    if search:
        stocks = stocks.filter(
            Q(product__name__icontains=search) | 
            Q(product__sku__icontains=search) |
            Q(location__name__icontains=search)
        )
    
    # Filter by location
    location_id = request.GET.get('location')
    if location_id:
        stocks = stocks.filter(location_id=location_id)
    
    # Filter by low stock
    low_stock = request.GET.get('low_stock')
    if low_stock == 'true':
        stocks = stocks.filter(quantity__lte=F('product__reorder_point'))
    
    locations = Location.objects.filter(is_active=True)
    
    context = {
        'stocks': stocks,
        'locations': locations,
        'search': search,
        # Add permissions
        'can_adjust': request.user.profile.can_adjust_stock(),
    }
    
    if request.htmx:
        return render(request, 'stock/partials/stock_table.html', context)
    
    return render(request, 'stock/stock_list.html', context)

@login_required
def stock_detail(request, pk):
    stock = get_object_or_404(Stock.objects.select_related('product', 'location'), pk=pk)
    
    # Get recent transactions for this product at this location
    recent_transactions = stock.product.transactions.filter(
        location=stock.location
    ).select_related('user').order_by('-created_at')[:20]
    
    context = {
        'stock': stock,
        'recent_transactions': recent_transactions,
        'can_adjust': request.user.profile.can_adjust_stock(),
    }
    
    return render(request, 'stock/stock_detail.html', context)

@login_required
@permission_required('can_adjust_stock')
def stock_adjustment(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            from transactions.models import Transaction, TransactionType
            
            adjustment_type = form.cleaned_data['adjustment_type']
            quantity = form.cleaned_data['quantity']
            notes = form.cleaned_data['notes']
            
            old_quantity = stock.quantity
            
            if adjustment_type == 'set':
                # Set to specific quantity
                Transaction.objects.create(
                    transaction_type=TransactionType.ADJUSTMENT,
                    product=stock.product,
                    location=stock.location,
                    quantity=quantity,
                    notes=f"Stock adjusted from {old_quantity} to {quantity}. {notes}",
                    user=request.user
                )
                stock.quantity = quantity
                stock.save()
                
                # Log activity
                log_activity(
                    user=request.user,
                    action='UPDATE',
                    model_name='Stock',
                    object_id=stock.id,
                    object_repr=f"{stock.product.name} at {stock.location.name}",
                    description=f'Adjusted stock from {old_quantity} to {quantity}',
                    request=request
                )
                
            elif adjustment_type == 'add':
                # Add quantity
                Transaction.objects.create(
                    transaction_type=TransactionType.ADJUSTMENT,
                    product=stock.product,
                    location=stock.location,
                    quantity=quantity,
                    notes=f"Added {quantity} units. {notes}",
                    user=request.user
                )
                
                # Log activity
                log_activity(
                    user=request.user,
                    action='UPDATE',
                    model_name='Stock',
                    object_id=stock.id,
                    object_repr=f"{stock.product.name} at {stock.location.name}",
                    description=f'Added {quantity} units (from {old_quantity} to {stock.quantity})',
                    request=request
                )
                
            elif adjustment_type == 'subtract':
                # Subtract quantity
                Transaction.objects.create(
                    transaction_type=TransactionType.DAMAGE,
                    product=stock.product,
                    location=stock.location,
                    quantity=quantity,
                    notes=f"Removed {quantity} units. {notes}",
                    user=request.user
                )
                
                # Log activity
                log_activity(
                    user=request.user,
                    action='UPDATE',
                    model_name='Stock',
                    object_id=stock.id,
                    object_repr=f"{stock.product.name} at {stock.location.name}",
                    description=f'Removed {quantity} units (from {old_quantity} to {stock.quantity})',
                    request=request
                )
            
            messages.success(request, 'Stock adjusted successfully!')
            
            if request.htmx:
                response = HttpResponse(status=204)
                response['HX-Redirect'] = f'/stock/{stock.pk}/'
                return response
            
            return redirect('stock:stock_detail', pk=stock.pk)
    else:
        form = StockAdjustmentForm()
    
    context = {
        'form': form,
        'stock': stock,
        'title': f'Adjust Stock - {stock.product.name}'
    }
    
    if request.htmx:
        return render(request, 'stock/partials/adjustment_form.html', context)
    
    return render(request, 'stock/stock_adjustment.html', context)

@login_required
def location_list(request):
    locations = Location.objects.all()
    
    # Annotate with total products and total stock value
    for location in locations:
        location.total_products = Stock.objects.filter(location=location).count()
        location.total_stock = Stock.objects.filter(location=location).aggregate(
            total=Sum('quantity')
        )['total'] or 0
    
    context = {
        'locations': locations,
        'can_manage': request.user.profile.can_manage_locations(),
    }
    return render(request, 'stock/location_list.html', context)

@login_required
@permission_required('can_manage_locations')
def location_create(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='CREATE',
                model_name='Location',
                object_id=location.id,
                object_repr=location.name,
                description=f'Created location: {location.code} - {location.name}',
                request=request
            )
            
            messages.success(request, f'Location {location.name} created successfully!')
            return redirect('stock:location_list')
    else:
        form = LocationForm()
    
    context = {'form': form, 'title': 'Create Location'}
    return render(request, 'stock/location_form.html', context)

@login_required
def stock_alerts(request):
    alerts = StockAlert.objects.select_related(
        'product', 'location'
    ).filter(is_resolved=False).order_by('-created_at')
    
    context = {'alerts': alerts}
    return render(request, 'stock/alerts.html', context)

@login_required
@permission_required('can_adjust_stock')
def resolve_alert(request, pk):
    alert = get_object_or_404(StockAlert, pk=pk)
    
    if request.method == 'POST':
        from django.utils import timezone
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        
        # Log activity
        log_activity(
            user=request.user,
            action='UPDATE',
            model_name='StockAlert',
            object_id=alert.id,
            object_repr=f"Alert for {alert.product.name}",
            description=f'Resolved {alert.get_alert_type_display()} alert',
            request=request
        )
        
        messages.success(request, 'Alert resolved!')
        
        if request.htmx:
            return HttpResponse(status=204)
        
        return redirect('stock:stock_alerts')
    
    return HttpResponse(status=405)