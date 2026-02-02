from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponse
from .models import Product, Category
from .forms import ProductForm, CategoryForm

@login_required
def product_list(request):
    products = Product.objects.select_related('category', 'supplier').all()
    
    # Search
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search) |
            Q(barcode__icontains=search)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by active status
    is_active = request.GET.get('is_active')
    if is_active:
        products = products.filter(is_active=is_active == 'true')
    
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'search': search,
    }
    
    if request.htmx:
        return render(request, 'products/partials/product_table.html', context)
    
    return render(request, 'products/product_list.html', context)

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category', 'supplier'), pk=pk)
    
    # Get stock levels across all locations
    stocks = product.stocks.select_related('location').all()
    
    # Get recent transactions
    recent_transactions = product.transactions.select_related('location', 'user').order_by('-created_at')[:10]
    
    context = {
        'product': product,
        'stocks': stocks,
        'recent_transactions': recent_transactions,
        'total_stock': sum(s.quantity for s in stocks),
    }
    
    return render(request, 'products/product_detail.html', context)

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product {product.name} created successfully!')
            
            if request.htmx:
                response = HttpResponse(status=204)
                response['HX-Redirect'] = product.get_absolute_url()
                return response
            
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProductForm()
    
    context = {'form': form, 'title': 'Create Product'}
    
    if request.htmx:
        return render(request, 'products/partials/product_form.html', context)
    
    return render(request, 'products/product_form.html', context)

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product {product.name} updated successfully!')
            
            if request.htmx:
                response = HttpResponse(status=204)
                response['HX-Redirect'] = product.get_absolute_url()
                return response
            
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    context = {'form': form, 'product': product, 'title': 'Update Product'}
    
    if request.htmx:
        return render(request, 'products/partials/product_form.html', context)
    
    return render(request, 'products/product_form.html', context)

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product {product_name} deleted successfully!')
        
        if request.htmx:
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse('products:product_list')
            return response
        
        return redirect('products:product_list')
    
    context = {'product': product}
    return render(request, 'products/product_confirm_delete.html', context)