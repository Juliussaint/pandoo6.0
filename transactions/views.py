from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from core.decorators import permission_required, log_activity
from .models import Transaction, TransactionType
from .forms import TransactionForm
from products.models import Product
from stock.models import Location

@login_required
def transaction_list(request):
    transactions = Transaction.objects.select_related(
        'product', 'location', 'user'
    ).all()
    
    # Search
    search = request.GET.get('search', '')
    if search:
        transactions = transactions.filter(
            Q(product__name__icontains=search) | 
            Q(product__sku__icontains=search) |
            Q(reference_number__icontains=search)
        )
    
    # Filter by type
    transaction_type = request.GET.get('type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    # Filter by location
    location_id = request.GET.get('location')
    if location_id:
        transactions = transactions.filter(location_id=location_id)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        transactions = transactions.filter(created_at__gte=date_from)
    if date_to:
        transactions = transactions.filter(created_at__lte=date_to)
    
    locations = Location.objects.filter(is_active=True)
    
    context = {
        'transactions': transactions[:100],  # Limit to recent 100
        'transaction_types': TransactionType.choices,
        'locations': locations,
        'search': search,
        'can_record': request.user.profile.can_record_transactions(),
    }
    
    if request.htmx:
        return render(request, 'transactions/partials/transaction_table.html', context)
    
    return render(request, 'transactions/transaction_list.html', context)

@login_required
def transaction_detail(request, pk):
    transaction = get_object_or_404(
        Transaction.objects.select_related('product', 'location', 'user'),
        pk=pk
    )
    
    context = {'transaction': transaction}
    return render(request, 'transactions/transaction_detail.html', context)

@login_required
@permission_required('can_record_transactions')
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='CREATE',
                model_name='Transaction',
                object_id=transaction.id,
                object_repr=f"{transaction.get_transaction_type_display()} - {transaction.product.name}",
                description=f'Recorded {transaction.get_transaction_type_display()} transaction: {transaction.quantity} units of {transaction.product.name}',
                request=request
            )
            
            messages.success(request, 'Transaction recorded successfully!')
            
            if request.htmx:
                response = HttpResponse(status=204)
                response['HX-Redirect'] = '/transactions/'
                return response
            
            return redirect('transactions:transaction_list')
    else:
        form = TransactionForm()
    
    context = {'form': form, 'title': 'Record Transaction'}
    
    if request.htmx:
        return render(request, 'transactions/partials/transaction_form.html', context)
    
    return render(request, 'transactions/transaction_form.html', context)