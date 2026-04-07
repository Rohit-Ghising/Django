from rest_framework import serializers

from .models import Order, OrderItem, Payment
from products.serializers import ProductSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'unit_price', 'total_price']

    def get_total_price(self, obj):
        return obj.total_price


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'method',
            'transaction_uuid',
            'amount',
            'tax_amount',
            'shipping_amount',
            'total_amount',
            'status',
            'created_at',
            'updated_at',
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'cart_id', 'total_price', 'status', 'created_at', 'items', 'payments']
