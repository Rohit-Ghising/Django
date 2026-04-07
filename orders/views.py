from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Order, Payment
from .serializers import OrderSerializer, PaymentSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_orders(request):
    if request.user.is_staff:
        orders = Order.objects.all().order_by('-created_at')
    else:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    query = Order.objects.all()
    if not request.user.is_staff:
        query = query.filter(user=request.user)
    order = get_object_or_404(query, pk=pk)
    serializer = OrderSerializer(order)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment(request, transaction_uuid):
    payment = get_object_or_404(Payment, transaction_uuid=transaction_uuid, order__user=request.user)
    status_flag = (request.data.get('status') or '').lower()
    if status_flag == 'success':
        payment.status = Payment.STATUS_SUCCESS
        payment.order.status = Order.STATUS_COMPLETED
        payment.order.save(update_fields=['status'])
    elif status_flag == 'failure':
        payment.status = Payment.STATUS_FAILED
        payment.order.status = Order.STATUS_PENDING
        payment.order.save(update_fields=['status'])
    else:
        return Response({'error': 'Invalid payment status'}, status=status.HTTP_400_BAD_REQUEST)

    payment.save()
    serializer = PaymentSerializer(payment)
    return Response(serializer.data)
