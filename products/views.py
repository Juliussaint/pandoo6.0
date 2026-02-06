from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponse
from django.urls import reverse
from core.decorators import permission_required, log_activity
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
        # Add permissions to context
        'can_create': request.user.profile.can_create_products(),
        'can_edit': request.user.profile.can_edit_products(),
        'can_delete': request.user.profile.can_delete_products(),
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
        # Add permissions
        'can_edit': request.user.profile.can_edit_products(),
        'can_delete': request.user.profile.can_delete_products(),
    }
    
    return render(request, 'products/product_detail.html', context)

@login_required
@permission_required('can_create_products')
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='CREATE',
                model_name='Product',
                object_id=product.id,
                object_repr=product.name,
                description=f'Created new product: {product.name}',
                request=request
            )
            
            messages.success(request, f'Product {product.name} created successfully!')
            
            # HTMX request - return 204 with HX-Redirect header
            if request.htmx:
                response = HttpResponse(status=204)
                response['HX-Redirect'] = reverse('products:product_list')
                return response
            
            # Regular request - normal redirect
            return redirect('products:product_list')
        else:
            # Form has errors - re-render with errors
            if request.htmx:
                context = {'form': form, 'title': 'Create Product'}
                return render(request, 'products/partials/product_form.html', context)
    else:
        form = ProductForm()
    
    context = {'form': form, 'title': 'Create Product'}
    
    if request.htmx:
        return render(request, 'products/partials/product_form.html', context)
    
    return render(request, 'products/product_form.html', context)

@login_required
@permission_required('can_edit_products')
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='UPDATE',
                model_name='Product',
                object_id=product.id,
                object_repr=product.name,
                description=f'Updated product: {product.name}',
                request=request
            )
            
            messages.success(request, f'Product {product.name} updated successfully!')
            
            # HTMX request
            if request.htmx:
                response = HttpResponse(status=204)
                response['HX-Redirect'] = reverse('products:product_list')
                return response
            
            return redirect('products:product_list')
        else:
            # Form has errors
            if request.htmx:
                context = {'form': form, 'product': product, 'title': 'Update Product'}
                return render(request, 'products/partials/product_form.html', context)
    else:
        form = ProductForm(instance=product)
    
    context = {'form': form, 'product': product, 'title': 'Update Product'}
    
    if request.htmx:
        return render(request, 'products/partials/product_form.html', context)
    
    return render(request, 'products/product_form.html', context)

@login_required
@permission_required('can_delete_products')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product_sku = product.sku
        
        # Log activity before deleting
        log_activity(
            user=request.user,
            action='DELETE',
            model_name='Product',
            object_id=product.id,
            object_repr=product_name,
            description=f'Deleted product: {product_sku} - {product_name}',
            request=request
        )
        
        product.delete()
        messages.success(request, f'Product {product_name} deleted successfully!')
        
        if request.htmx:
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse('products:product_list')
            return response
        
        return redirect('products:product_list')
    
    context = {'product': product}
    return render(request, 'products/product_confirm_delete.html', context)


@login_required
@permission_required('can_view_products')
def category_list(request):
    categories = Category.objects.annotate(
        product_count=Count('products')
    ).all()
    
    # Search
    search = request.GET.get('search', '')
    if search:
        categories = categories.filter(name__icontains=search)
    
    context = {
        'categories': categories,
        'search': search,
        'can_create': request.user.profile.can_create_products(),
        'can_edit': request.user.profile.can_edit_products(),
        'can_delete': request.user.profile.can_delete_products(),
    }
    
    if request.htmx:
        return render(request, 'products/partials/category_table.html', context)
    
    return render(request, 'products/category_list.html', context)

@login_required
@permission_required('can_view_products')
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    # Get products in this category
    products = category.products.all()
    
    # Get subcategories
    subcategories = category.subcategories.all()
    
    context = {
        'category': category,
        'products': products,
        'subcategories': subcategories,
    }
    
    return render(request, 'products/category_detail.html', context)

@login_required
@permission_required('can_create_products')
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category {category.name} created successfully!')
            
            if request.htmx:
                response = HttpResponse(status=204)
                response['HX-Redirect'] = f'/products/categories/{category.pk}/'
                return response
            
            return redirect('products:category_detail', pk=category.pk)
    else:
        form = CategoryForm()
    
    context = {'form': form, 'title': 'Create Category'}
    
    if request.htmx:
        return render(request, 'products/partials/category_form.html', context)
    
    return render(request, 'products/category_form.html', context)

@login_required
@permission_required('can_edit_products')
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category {category.name} updated successfully!')
            
            if request.htmx:
                response = HttpResponse(status=204)
                response['HX-Redirect'] = f'/products/categories/{category.pk}/'
                return response
            
            return redirect('products:category_detail', pk=category.pk)
    else:
        form = CategoryForm(instance=category)
    
    context = {'form': form, 'category': category, 'title': 'Update Category'}
    
    if request.htmx:
        return render(request, 'products/partials/category_form.html', context)
    
    return render(request, 'products/category_form.html', context)

@login_required
@permission_required('can_delete_products')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    # Check if category has products
    if category.products.exists():
        messages.error(request, f'Cannot delete category {category.name} because it has products!')
        return redirect('products:category_detail', pk=category.pk)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category {category_name} deleted successfully!')
        
        return redirect('products:category_list')
    
    context = {'category': category}
    return render(request, 'products/category_confirm_delete.html', context)