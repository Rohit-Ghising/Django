from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Order
from .serializers import OrderSerializer


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
