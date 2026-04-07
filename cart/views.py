import base64
import hashlib
import hmac
from decimal import Decimal
from uuid import uuid4

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Cart, CartItem
from .serializers import CartSerializer, AddCartItemSerializer, UpdateCartItemSerializer
from products.models import Product
from orders.models import Order, OrderItem, Payment
from orders.serializers import OrderSerializer, PaymentSerializer


def build_frontend_redirect(path: str) -> str:
    base_url = settings.ESEWA_FRONTEND_BASE_URL.rstrip('/')
    if not base_url:
        return path
    if path.startswith('/'):
        return f'{base_url}{path}'
    return f'{base_url}/{path}'


def build_esewa_redirect_url(status_value: str, transaction_uuid: str) -> str:
    base_redirect = (
        settings.ESEWA_SUCCESS_REDIRECT if status_value == 'success' else settings.ESEWA_FAILURE_REDIRECT
    )
    fallback_path = f'/checkout?payment=esewa_{status_value}&payment_uuid={transaction_uuid}'
    base_url = base_redirect or build_frontend_redirect(fallback_path)
    separator = '&' if '?' in base_url else '?'
    if 'payment_uuid=' in base_url:
        return base_url
    if 'payment=' in base_url or 'esewa_status=' in base_url:
        return f'{base_url}{separator}payment_uuid={transaction_uuid}'
    status_key = 'payment'
    status_field = f'esewa_{status_value}'
    return f'{base_url}{separator}{status_key}={status_field}&payment_uuid={transaction_uuid}'


def generate_esewa_signature(total_amount: Decimal, transaction_uuid: str, product_code: str) -> str:
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    digest = hmac.new(
        settings.ESEWA_SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode('utf-8')

# Get or create active cart for user
def get_user_cart(user):
    cart, created = Cart.objects.get_or_create(user=user, is_ordered=False)
    return cart

# List user's cart
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    cart = get_user_cart(request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)

# Add product to cart
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    serializer = AddCartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    product_id = serializer.validated_data['product_id']
    quantity = serializer.validated_data['quantity']
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    cart = get_user_cart(request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity},
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    cart_serializer = CartSerializer(cart)
    return Response(cart_serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    cart = get_user_cart(request.user)
    cart.items.all().delete()
    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_cart(request):
    cart = get_user_cart(request.user)
    if not cart.items.exists():
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    cart_items = list(cart.items.select_related('product'))
    order_total = sum(Decimal(item.total_price) for item in cart_items)
    order_total = order_total.quantize(Decimal('0.01'))
    shipping_fee = Decimal('0.00') if order_total > Decimal('99.00') else Decimal('9.99')
    tax_amount = (order_total * Decimal('0.08')).quantize(Decimal('0.01'))
    total_amount = (order_total + shipping_fee + tax_amount).quantize(Decimal('0.01'))

    order = Order.objects.create(
        user=request.user,
        cart_id=cart.id,
        total_price=order_total,
        status=Order.STATUS_PENDING,
    )

    order_items = []
    for item in cart_items:
        unit_price = item.product.discount_price if item.product.discount_price else item.product.price
        order_items.append(OrderItem(
            order=order,
            product=item.product,
            quantity=item.quantity,
            unit_price=unit_price,
        ))
    OrderItem.objects.bulk_create(order_items)

    cart.items.all().delete()
    cart.is_ordered = True
    cart.save()
    new_cart = get_user_cart(request.user)
    payment = Payment.objects.create(
        order=order,
        method=Payment.METHOD_ESEWA,
        transaction_uuid=uuid4().hex,
        amount=order_total,
        tax_amount=tax_amount,
        shipping_amount=shipping_fee,
        total_amount=total_amount,
    )

    signed_field_names = "total_amount,transaction_uuid,product_code"
    signature = generate_esewa_signature(
        total_amount=total_amount,
        transaction_uuid=payment.transaction_uuid,
        product_code=settings.ESEWA_MERCHANT_ID,
    )
    esewa_payload = {
        "payment_url": settings.ESEWA_PAYMENT_URL,
        "product_code": settings.ESEWA_MERCHANT_ID,
        "amount": str(order_total),
        "tax_amount": str(tax_amount),
        "total_amount": str(total_amount),
        "transaction_uuid": payment.transaction_uuid,
        "product_service_charge": "0",
        "product_delivery_charge": str(shipping_fee),
        "success_url": build_esewa_redirect_url('success', payment.transaction_uuid),
        "failure_url": build_esewa_redirect_url('failure', payment.transaction_uuid),
        "signed_field_names": signed_field_names,
        "signature": signature,
    }

    cart_serializer = CartSerializer(new_cart)
    order_serializer = OrderSerializer(order)
    payment_serializer = PaymentSerializer(payment)
    return Response({
        'message': 'Checkout complete',
        'order': order_serializer.data,
        'payment': payment_serializer.data,
        'esewa': esewa_payload,
        'cart': cart_serializer.data,
    })

# Update quantity
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user, cart__is_ordered=False)
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = UpdateCartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    cart_item.quantity = serializer.validated_data['quantity']
    cart_item.save()
    cart = get_user_cart(request.user)
    cart_serializer = CartSerializer(cart)
    return Response(cart_serializer.data)

# Remove item from cart
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user, cart__is_ordered=False)
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
    
    cart_item.delete()
    cart = get_user_cart(request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)
