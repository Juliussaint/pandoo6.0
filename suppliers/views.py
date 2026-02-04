from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.http import HttpResponse
from core.decorators import permission_required, log_activity
from .models import Supplier
from .forms import SupplierForm

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.annotate(
        product_count=Count('products'),
        po_count=Count('purchase_orders')
    ).all()
    
    # Search
    search = request.GET.get('search', '')
    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Filter by active status
    is_active = request.GET.get('is_active')
    if is_active:
        suppliers = suppliers.filter(is_active=is_active == 'true')
    
    context = {
        'suppliers': suppliers,
        'search': search,
        'can_create': request.user.profile.can_create_suppliers(),
        'can_edit': request.user.profile.can_edit_suppliers(),
        'can_delete': request.user.profile.can_delete_suppliers(),
    }
    
    return render(request, 'suppliers/supplier_list.html', context)

@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    # Get products from this supplier
    products = supplier.products.all()[:10]
    
    # Get recent purchase orders
    purchase_orders = supplier.purchase_orders.order_by('-created_at')[:10]
    
    context = {
        'supplier': supplier,
        'products': products,
        'purchase_orders': purchase_orders,
        'can_edit': request.user.profile.can_edit_suppliers(),
        'can_delete': request.user.profile.can_delete_suppliers(),
    }
    
    return render(request, 'suppliers/supplier_detail.html', context)

@login_required
@permission_required('can_create_suppliers')
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='CREATE',
                model_name='Supplier',
                object_id=supplier.id,
                object_repr=supplier.name,
                description=f'Created supplier: {supplier.name}',
                request=request
            )
            
            messages.success(request, f'Supplier {supplier.name} created successfully!')
            
            if request.htmx:
                response = HttpResponse(status=204)
                response['HX-Redirect'] = f'/suppliers/{supplier.pk}/'
                return response
            
            return redirect('suppliers:supplier_detail', pk=supplier.pk)
    else:
        form = SupplierForm()
    
    context = {'form': form, 'title': 'Create Supplier'}
    
    if request.htmx:
        return render(request, 'suppliers/partials/supplier_form.html', context)
    
    return render(request, 'suppliers/supplier_form.html', context)

@login_required
@permission_required('can_edit_suppliers')
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            supplier = form.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='UPDATE',
                model_name='Supplier',
                object_id=supplier.id,
                object_repr=supplier.name,
                description=f'Updated supplier: {supplier.name}',
                request=request
            )
            
            messages.success(request, f'Supplier {supplier.name} updated successfully!')
            
            if request.htmx:
                response = HttpResponse(status=204)
                response['HX-Redirect'] = f'/suppliers/{supplier.pk}/'
                return response
            
            return redirect('suppliers:supplier_detail', pk=supplier.pk)
    else:
        form = SupplierForm(instance=supplier)
    
    context = {'form': form, 'supplier': supplier, 'title': 'Update Supplier'}
    
    if request.htmx:
        return render(request, 'suppliers/partials/supplier_form.html', context)
    
    return render(request, 'suppliers/supplier_form.html', context)

@login_required
@permission_required('can_delete_suppliers')
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        supplier_name = supplier.name
        
        # Log activity before deleting
        log_activity(
            user=request.user,
            action='DELETE',
            model_name='Supplier',
            object_id=supplier.id,
            object_repr=supplier_name,
            description=f'Deleted supplier: {supplier_name}',
            request=request
        )
        
        supplier.delete()
        messages.success(request, f'Supplier {supplier_name} deleted successfully!')
        
        return redirect('suppliers:supplier_list')
    
    context = {'supplier': supplier}
    return render(request, 'suppliers/supplier_confirm_delete.html', context)