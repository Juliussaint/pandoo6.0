from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.urls import reverse
from core.decorators import permission_required, log_activity
from .models import PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem
from .forms import PurchaseOrderForm, PurchaseOrderItemFormSet, GoodsReceiptForm
from transactions.models import Transaction, TransactionType

@login_required
@permission_required('can_view_reports')
def purchase_order_list(request):
    purchase_orders = PurchaseOrder.objects.select_related(
        'supplier', 'location', 'created_by'
    ).all()
    
    # Search
    search = request.GET.get('search', '')
    if search:
        purchase_orders = purchase_orders.filter(
            Q(po_number__icontains=search) | 
            Q(supplier__name__icontains=search)
        )
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        purchase_orders = purchase_orders.filter(status=status)
    
    # Filter by supplier
    supplier_id = request.GET.get('supplier')
    if supplier_id:
        purchase_orders = purchase_orders.filter(supplier_id=supplier_id)
    
    from suppliers.models import Supplier
    suppliers = Supplier.objects.filter(is_active=True)
    
    context = {
        'purchase_orders': purchase_orders,
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'suppliers': suppliers,
        'search': search,
        'can_create': request.user.profile.can_create_purchase_orders(),
        'can_edit': request.user.profile.can_edit_purchase_orders(),
        'can_delete': request.user.profile.can_delete_purchase_orders(),
        'can_receive': request.user.profile.can_receive_goods(),
    }
    
    if request.htmx:
        return render(request, 'purchases/partials/po_table.html', context)
    
    return render(request, 'purchases/purchase_order_list.html', context)

@login_required
@permission_required('can_view_reports')
def purchase_order_detail(request, pk):
    po = get_object_or_404(
        PurchaseOrder.objects.select_related('supplier', 'location', 'created_by'),
        pk=pk
    )
    
    items = po.items.select_related('product').all()
    receipts = po.receipts.select_related('received_by').prefetch_related('items').all()
    
    context = {
        'po': po,
        'items': items,
        'receipts': receipts,
        'can_edit': request.user.profile.can_edit_purchase_orders(),
        'can_delete': request.user.profile.can_delete_purchase_orders(),
        'can_receive': request.user.profile.can_receive_goods(),
    }
    
    return render(request, 'purchases/purchase_order_detail.html', context)

@login_required
@permission_required('can_create_purchase_orders')
def purchase_order_create(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        formset = PurchaseOrderItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()
            
            formset.instance = po
            formset.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='CREATE',
                model_name='PurchaseOrder',
                object_id=po.id,
                object_repr=po.po_number,
                description=f'Created purchase order {po.po_number} for {po.supplier.name}',
                request=request
            )
            
            messages.success(request, f'Purchase Order {po.po_number} created successfully!')
            return redirect('purchases:purchase_order_detail', pk=po.pk)
    else:
        form = PurchaseOrderForm()
        formset = PurchaseOrderItemFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Purchase Order'
    }
    
    return render(request, 'purchases/purchase_order_form.html', context)

@login_required
@permission_required('can_edit_purchase_orders')
def purchase_order_update(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    if po.status not in ['DRAFT', 'SENT']:
        messages.error(request, 'Cannot edit a purchase order that has been received or cancelled.')
        return redirect('purchases:purchase_order_detail', pk=po.pk)
    
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po)
        formset = PurchaseOrderItemFormSet(request.POST, instance=po)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='UPDATE',
                model_name='PurchaseOrder',
                object_id=po.id,
                object_repr=po.po_number,
                description=f'Updated purchase order {po.po_number}',
                request=request
            )
            
            messages.success(request, f'Purchase Order {po.po_number} updated successfully!')
            return redirect('purchases:purchase_order_detail', pk=po.pk)
    else:
        form = PurchaseOrderForm(instance=po)
        formset = PurchaseOrderItemFormSet(instance=po)
    
    context = {
        'form': form,
        'formset': formset,
        'po': po,
        'title': 'Update Purchase Order'
    }
    
    return render(request, 'purchases/purchase_order_form.html', context)

@login_required
@permission_required('can_approve_purchase_orders')
def purchase_order_send(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    if request.method == 'POST':
        if po.status == 'DRAFT':
            po.status = 'SENT'
            po.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='UPDATE',
                model_name='PurchaseOrder',
                object_id=po.id,
                object_repr=po.po_number,
                description=f'Sent purchase order {po.po_number} to supplier',
                request=request
            )
            
            messages.success(request, f'Purchase Order {po.po_number} sent to supplier!')
        else:
            messages.error(request, 'Can only send draft purchase orders.')
        
        return redirect('purchases:purchase_order_detail', pk=po.pk)
    
    return HttpResponse(status=405)

@login_required
@permission_required('can_delete_purchase_orders')
def purchase_order_cancel(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    if request.method == 'POST':
        if po.status in ['DRAFT', 'SENT']:
            po.status = 'CANCELLED'
            po.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='UPDATE',
                model_name='PurchaseOrder',
                object_id=po.id,
                object_repr=po.po_number,
                description=f'Cancelled purchase order {po.po_number}',
                request=request
            )
            
            messages.success(request, f'Purchase Order {po.po_number} cancelled!')
        else:
            messages.error(request, 'Cannot cancel this purchase order.')
        
        return redirect('purchases:purchase_order_detail', pk=po.pk)
    
    return HttpResponse(status=405)

@login_required
@permission_required('can_receive_goods')
def goods_receipt_create(request, po_pk):
    po = get_object_or_404(PurchaseOrder, pk=po_pk)
    
    if po.status == 'CANCELLED':
        messages.error(request, 'Cannot receive goods for a cancelled purchase order.')
        return redirect('purchases:purchase_order_detail', pk=po.pk)
    
    if request.method == 'POST':
        form = GoodsReceiptForm(request.POST)
        
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.purchase_order = po
            receipt.received_by = request.user
            receipt.save()
            
            # Process received items
            for item_id, quantity in request.POST.items():
                if item_id.startswith('item_'):
                    po_item_id = int(item_id.replace('item_', ''))
                    quantity_received = int(quantity) if quantity else 0
                    
                    if quantity_received > 0:
                        po_item = PurchaseOrderItem.objects.get(pk=po_item_id)
                        
                        # Create goods receipt item
                        GoodsReceiptItem.objects.create(
                            goods_receipt=receipt,
                            po_item=po_item,
                            quantity_received=quantity_received
                        )
                        
                        # Update PO item received quantity
                        po_item.received_quantity += quantity_received
                        po_item.save()
                        
                        # Create transaction
                        Transaction.objects.create(
                            transaction_type=TransactionType.PURCHASE,
                            product=po_item.product,
                            location=po.location,
                            quantity=quantity_received,
                            unit_price=po_item.unit_price,
                            reference_number=receipt.receipt_number,
                            notes=f"Goods received from PO {po.po_number}",
                            user=request.user
                        )
            
            # Update PO status
            all_items = po.items.all()
            fully_received = all(item.received_quantity >= item.quantity for item in all_items)
            partially_received = any(item.received_quantity > 0 for item in all_items)
            
            if fully_received:
                po.status = 'RECEIVED'
                po.actual_delivery = timezone.now().date()
            elif partially_received:
                po.status = 'PARTIAL'
            
            po.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='CREATE',
                model_name='GoodsReceipt',
                object_id=receipt.id,
                object_repr=receipt.receipt_number,
                description=f'Received goods for PO {po.po_number}',
                request=request
            )
            
            messages.success(request, f'Goods Receipt {receipt.receipt_number} created successfully!')
            return redirect('purchases:purchase_order_detail', pk=po.pk)
    else:
        # Generate receipt number
        import uuid
        receipt_number = f"GR-{uuid.uuid4().hex[:8].upper()}"
        
        form = GoodsReceiptForm(initial={
            'receipt_number': receipt_number,
            'received_date': timezone.now().date()
        })
    
    items = po.items.select_related('product').all()
    
    context = {
        'form': form,
        'po': po,
        'items': items,
        'title': f'Receive Goods - PO {po.po_number}'
    }
    
    return render(request, 'purchases/goods_receipt_form.html', context)